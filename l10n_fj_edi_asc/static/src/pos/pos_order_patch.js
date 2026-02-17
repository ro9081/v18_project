/** @odoo-module **/
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    setup() {
        super.setup();
        this.verification_qr = this.rawData.verification_qr || "";
    },

    export_for_printing(base_url, header_data) {
        const result = super.export_for_printing(base_url, header_data);
        result.verification_qr = this.verification_qr;
        return result;
    }
});
