from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Dict, List, Optional

from django.apps import apps
from django.db import transaction
from django.db.models.fields.related import ManyToOneRel, OneToOneRel, ManyToManyRel
from django.contrib.auth import get_user_model

from .models import (
    InventoryMaster,
    VendorItem,              # FK: item -> InventoryMaster  (unique together: vendor + item)
    PriceHistory,            # FK: item -> InventoryMaster
    PurchaseLine,            # FK: item -> InventoryMaster
    InventoryPricingGroup,   # FK: inventory -> InventoryMaster (unique together: inventory + group)
    InventoryMergeLog,
)
from workorders.models import WorkorderItem  # FK: inventory_item -> InventoryMaster

User = get_user_model()

# -------------------------------------------------------------------
# Helpers to introspect relationships to InventoryMaster
# -------------------------------------------------------------------

def _iter_fk_rels_to_master():
    """
    Yield (RelatedModel, fk_field_name) for every model that FK's to InventoryMaster.
    """
    for rel in InventoryMaster._meta.get_fields():
        if isinstance(rel, ManyToOneRel) and rel.related_model is not None:
            yield rel.related_model, rel.field.name

def _iter_m2m_rels_of_master():
    """
    Yield M2M fields where InventoryMaster participates (both auto and custom through).
    """
    for rel in InventoryMaster._meta.get_fields():
        if isinstance(rel, ManyToManyRel):
            yield rel

def _model_key(model):
    return f"{model._meta.app_label}.{model.__name__}"

# Dedupe rules for tables with unique constraints that can clash after retargeting.
# key = "app.Model", value = {"fk_field": "<name>", "unique_together": (<field1>, <field2>, ...)}
SPECIAL_HANDLERS = {
    _model_key(VendorItem): {
        "fk_field": "item",
        "unique_together": ("vendor", "item"),
    },
    _model_key(InventoryPricingGroup): {
        "fk_field": "inventory",
        "unique_together": ("inventory", "group"),
    },
}

# -------------------------------------------------------------------
# Merge / Unmerge
# -------------------------------------------------------------------

@transaction.atomic
def merge_inventory_items(
    target: InventoryMaster,
    dups: Iterable[InventoryMaster],
    user: Optional[User] = None,
    prefer_target_name: bool = True,
) -> InventoryMergeLog:
    """
    Merge duplicate InventoryMaster rows into 'target'.

    Moves FK relations from each dup -> target, dedupes rows that would violate
    uniques, soft-deletes dup (is_active=False, merged_into=target), and logs
    exactly what was moved so unmerge can reverse most changes.
    """
    target = InventoryMaster.objects.select_for_update().get(pk=target.pk)
    dups = [d for d in dups if d.pk and d.pk != target.pk]
    dup_ids = [d.pk for d in dups]

    details = {
        "fk_moves": defaultdict(lambda: defaultdict(list)),   # { "app.Model.fk": {dup_id:[ids]} }
        "m2m_added": defaultdict(lambda: defaultdict(list)),  # { dup_id: { "app.Model.field":[ids] } }
        "special": defaultdict(list),                         # { "app.Model.fk": [snapshots…] }
        "skipped_one_to_one": defaultdict(list),              # { "app.Model.fk":[dup_id,…] }
    }
    previous_names = {d.pk: (d.name or "") for d in dups}

    # 1) Repoint FK relations (with dedupe for special tables)
    for RelModel, fk_field in _iter_fk_rels_to_master():
        key = f"{_model_key(RelModel)}.{fk_field}"

        # Skip if this is effectively a reverse OneToOne (avoid unique clashes)
        if any(isinstance(f, OneToOneRel) and f.related_model is RelModel for f in InventoryMaster._meta.get_fields()):
            details["skipped_one_to_one"][key].extend(dup_ids)
            continue

        handler = SPECIAL_HANDLERS.get(_model_key(RelModel))
        if handler and handler.get("fk_field") == fk_field:
            # Dedupe-aware move (e.g., VendorItem, InventoryPricingGroup)
            uniq = handler["unique_together"]
            uniq_attnames = []
            for fname in uniq:
                # Use the DB column attname (handles *_id on FKs)
                field = RelModel._meta.get_field(fname)
                uniq_attnames.append(field.attname)

            for dup in dups:
                rows = list(RelModel.objects.filter(**{fk_field: dup.pk}))
                for r in rows:
                    # Identify potential conflicting target row
                    lookup = {fk_field: target.pk}
                    for att in uniq_attnames:
                        lookup[att] = getattr(r, att)
                    existing = RelModel.objects.filter(**lookup).first()

                    if existing:
                        # Snapshot for unmerge
                        details["special"][key].append({
                            "action": "merge_delete",
                            "dup_row": {"id": r.id, "snapshot": _row_snapshot(r)},
                            "existing_row": {"id": existing.id, "prev": _row_snapshot(existing)},
                        })
                        # Coalesce non-null fields from dup into existing
                        changed = []
                        for f in r._meta.concrete_fields:
                            if f.attname in ("id", fk_field + "_id"):
                                continue
                            val = getattr(r, f.attname)
                            if val not in (None, "", []):
                                if getattr(existing, f.attname) in (None, "", []):
                                    setattr(existing, f.attname, val)
                                    changed.append(f.attname)
                        if changed:
                            existing.save(update_fields=list(set(changed)))
                        r.delete()
                    else:
                        # Normal retarget
                        details["fk_moves"][key][dup.pk].append(r.id)
                        setattr(r, fk_field + "_id", target.pk)
                        r.save(update_fields=[fk_field])
        else:
            # Plain bulk update for simple FKs
            per_dup_ids: List[int] = []
            for dup in dups:
                ids = list(RelModel.objects.filter(**{f"{fk_field}_id": dup.pk}).values_list("id", flat=True))
                if ids:
                    details["fk_moves"][key][dup.pk].extend(ids)
                    per_dup_ids.extend(ids)
            if per_dup_ids:
                RelModel.objects.filter(id__in=per_dup_ids).update(**{fk_field: target})

    # 2) Union M2Ms
    for dup in dups:
        for rel in _iter_m2m_rels_of_master():
            field_key = f"{_model_key(rel.model)}.{rel.name}"
            t_mgr = getattr(target, rel.name)
            d_mgr = getattr(dup, rel.name)

            if rel.through._meta.auto_created:
                ids = list(d_mgr.values_list("pk", flat=True))
                if ids:
                    t_mgr.add(*ids)
                    details["m2m_added"][dup.pk][field_key] = ids
            else:
                # Custom through: reassign the FK column that points to InventoryMaster
                item_fk_name = None
                for f in rel.through._meta.fields:
                    if getattr(f, "related_model", None) is InventoryMaster or (
                        getattr(f, "remote_field", None) and f.remote_field.model is InventoryMaster
                    ):
                        item_fk_name = f.name
                        break
                if item_fk_name:
                    through_qs = rel.through.objects.filter(**{f"{item_fk_name}_id": dup.pk})
                    ids = list(through_qs.values_list("id", flat=True))
                    if ids:
                        through_qs.update(**{item_fk_name: target})
                        details["m2m_added"][dup.pk][f"{_model_key(rel.through)}.{item_fk_name}"] = ids

    # 3) Optional name borrow
    if not prefer_target_name and not (target.name or "").strip():
        donor = next((d for d in dups if (d.name or "").strip()), None)
        if donor:
            target.name = donor.name
            target.save(update_fields=["name"])

    # 4) Soft delete duplicates + mark merged_into
    InventoryMaster.objects.filter(pk__in=dup_ids).update(is_active=False, merged_into=target)

    log = InventoryMergeLog.objects.create(
        user=user,
        target=target,
        merged_ids=dup_ids,
        details=_dictify(details),
        previous_names=previous_names,
        note=f"Merged {len(dup_ids)} item(s) into {target.pk}",
    )
    return log


@transaction.atomic
def unmerge_inventory_items(merge_log_id: int, user: Optional[User] = None) -> Dict[str, List[int]]:
    """
    Reverse a merge using the stored InventoryMergeLog.

    Restores:
      - FK rows moved via bulk updates (fk_moves)
      - Rows modified/deleted due to unique dedupe (special)
      - M2M links added to target (m2m_added)
      - Reactivates dup masters and clears merged_into
      - Restores previous names
    """
    log = InventoryMergeLog.objects.select_for_update().get(pk=merge_log_id)
    target = log.target
    dup_ids = list(log.merged_ids or [])
    details = log.details or {}
    previous_names = log.previous_names or {}

    # 1) Undo FK moves
    for key, per_dup in (details.get("fk_moves") or {}).items():
        app_model, fk_field = key.rsplit(".", 1)
        app_label, model_name = app_model.split(".")
        Model = apps.get_model(app_label, model_name)
        for dup_id, ids_ in per_dup.items():
            if ids_:
                Model.objects.filter(id__in=ids_).update(**{fk_field: dup_id})

    # 2) Undo special merge/deletes (recreate deleted dup rows, restore modified existing)
    for key, actions in (details.get("special") or {}).items():
        app_model, fk_field = key.rsplit(".", 1)
        app_label, model_name = app_model.split(".")
        Model = apps.get_model(app_label, model_name)
        for act in actions:
            if act.get("action") != "merge_delete":
                continue
            # Restore existing row fields
            ex_id = act["existing_row"]["id"]
            prev = act["existing_row"]["prev"]
            Model.objects.filter(id=ex_id).update(**_snapshot_to_update(Model, prev))
            # Recreate deleted dup row
            snap = dict(act["dup_row"]["snapshot"])
            snap.pop("id", None)
            snap.pop("_state", None)
            Model.objects.create(**snap)

    # 3) Undo M2M adds (auto-through and custom-through)
    for dup_id, by_field in (details.get("m2m_added") or {}).items():
        for field_key, ids_ in by_field.items():
            app_model, field_or_fk = field_key.rsplit(".", 1)
            app_label, model_name = app_model.split(".")
            Model = apps.get_model(app_label, model_name)
            if hasattr(InventoryMaster, field_or_fk):
                # Auto M2M: remove links from target
                getattr(target, field_or_fk).remove(*ids_)
            else:
                # Custom-through: revert FK on through rows
                Through = Model
                Through.objects.filter(id__in=ids_).update(**{field_or_fk: dup_id})

    # 4) Reactivate dup masters and restore names
    InventoryMaster.objects.filter(pk__in=dup_ids).update(is_active=True, merged_into=None)
    for k, old in previous_names.items():
        try:
            m = InventoryMaster.objects.get(pk=int(k))
            if m.name != old:
                m.name = old
                m.save(update_fields=["name"])
        except (InventoryMaster.DoesNotExist, ValueError):
            pass

    InventoryMergeLog.objects.create(
        user=user,
        target=target,
        merged_ids=dup_ids,
        details={"unmerge_of": merge_log_id},
        note="Unmerged prior merge",
    )
    return {"restored_items": dup_ids, "from_merge_log": merge_log_id}

# -------------------------------------------------------------------
# Small utilities
# -------------------------------------------------------------------

def _row_snapshot(obj):
    """
    Return a plain snapshot dict of concrete fields suitable for later recreation.
    Includes *_id for FK columns.
    """
    snap = {}
    for f in obj._meta.concrete_fields:
        snap[f.attname] = getattr(obj, f.attname)
    return snap

def _snapshot_to_update(Model, snap: Dict) -> Dict:
    """
    Turn a snapshot into an update dict for Model.objects.filter(...).update(**dict).
    """
    allowed = {f.attname for f in Model._meta.concrete_fields} - {"id"}
    return {k: v for k, v in snap.items() if k in allowed}

def _dictify(details):
    """
    Convert defaultdict nesting into plain dicts for JSONField.
    """
    def d(x):
        if isinstance(x, defaultdict):
            return {k: d(v) for k, v in x.items()}
        if isinstance(x, dict):
            return {k: d(v) for k, v in x.items()}
        if isinstance(x, list):
            return [d(v) for v in x]
        return x
    return d(details)