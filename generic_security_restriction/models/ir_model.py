from odoo import api, models, fields
from lxml import etree
from odoo.models import BaseModel


class IrModel(models.Model):
    _inherit = 'ir.model'

    field_security_ids = fields.One2many(
        'generic.security.restriction.field', 'model_id',
        index=True, string='Security Fields')

class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        if operation in ('create', 'write') and self._name not in self.env.user.model_ids.mapped('model') and not self.env.user.has_group('base.group_system'):
            return False
        if operation == 'unlink' and self._name not in self.env.user.delete_model_ids.mapped('model') and not self.env.user.has_group('base.group_system'):
            return False
        return self.env['ir.model.access'].check(self._name, operation, raise_exception)

fields_view_get_extra = BaseModel.fields_view_get 

def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    result = fields_view_get_extra(self,view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    if self._name not in self.env.user.duplicate_model_ids.mapped('model'):
        temp = etree.fromstring(result['arch'])
        temp.set('duplicate','false')
        result['arch'] = etree.tostring(temp)
    return result

BaseModel.fields_view_get = fields_view_get
