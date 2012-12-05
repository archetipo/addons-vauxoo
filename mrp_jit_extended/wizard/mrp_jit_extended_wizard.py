# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
############################################################################
#    Coded by: fernandoL (fernando_ld@vauxoo.com)
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import osv, fields
from tools.translate import _
import netsvc

class procurement_order_merge_jit_extended(osv.osv_memory):
    _name = 'procurement.order.merge.jit.extended'

    def procurement_merge_jit(self, cr, uid, ids, context=None, rec_ids=None):
        procurement_order_pool = self.pool.get('procurement.order')
        mrp_production_pool = self.pool.get('mrp.production')
        if context is None:
            context = {}
        if rec_ids is None:
            production_ids = context.get('active_ids', [])
        else:
            production_ids = rec_ids
        procurement_ids = []
        for production_id in production_ids:
            production_data = mrp_production_pool.browse(cr, uid, production_id, context=context)
            for line in production_data.procurement_ids:
                if (line.state == 'draft') and (line.product_id.supply_method=='produce'):
                    procurement_ids.append(line.id)

        res = procurement_order_pool.do_merge(cr, uid, procurement_ids, context=context)
        
        #forwards procurements that were not merged and its product is to produce
        wf_service = netsvc.LocalService("workflow")
        for production_id in production_ids:
            production_data = mrp_production_pool.browse(cr, uid, production_id, context=context)
            for line in production_data.procurement_ids:
                if (line.state == 'draft') and (line.product_id.supply_method=='produce') and (line.product_id.type <> 'service'):
                    wf_service.trg_validate(uid, 'procurement.order', line.id, 'button_confirm', cr)
                    wf_service.trg_validate(uid, 'procurement.order', line.id, 'button_check', cr)
                    procurements = self.pool.get('procurement.order').read(cr, uid, line.id, ['production_created'], context=context)
                    new_production_id_tup = procurements.get('production_created')
                    if new_production_id_tup:
                        new_production_id = new_production_id_tup[0]
                        res[0].append(new_production_id)

        if res[0]:
            for line in res[1]:
                mrp_production_pool.write(cr, uid, res[0], {'subproduction_ids': [(4, line)]})
            self.procurement_merge_jit(cr, uid, ids, context, res[0])
        return {}

procurement_order_merge_jit_extended()