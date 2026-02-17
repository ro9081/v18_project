/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;

        // ✅ Step 1: Store whether invoice checkbox is true
        const isToInvoice = order.is_to_invoice();

        // ✅ Step 2: Validate order as usual
        await super.validateOrder(isForceValidate);

        // ✅ Step 3: If invoice was enabled, wait for invoice ID
        if (isToInvoice) {
            for (let i = 0; i < 10; i++) {
                if (order.account_move) {
                    // ✅ Step 4: Call custom API
                    await fetch(`/api/verification/code?move_id=${order.account_move}`);
                    return;
                }
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            console.warn("⚠️ Invoice was not created in time.");
        }
    },
});
