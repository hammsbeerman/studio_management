from django.test import TestCase

class ItemPricingGroupExistsTests(TestCase):
    def test_model_exists_and_can_save(self):
        # import inside test so it fails loudly if model vanished
        from inventory.models import ItemPricingGroup
        obj = ItemPricingGroup.objects.create(name="Sheets")
        self.assertIsNotNone(obj.pk)