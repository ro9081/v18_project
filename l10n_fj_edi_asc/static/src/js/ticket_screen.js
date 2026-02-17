/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { rpc } from "@web/core/network/rpc";
patch(TicketScreen.prototype, {
    async onClickPopup() {
          const order = this.getSelectedOrder?.() || this.selectedOrder;
        console.log("Selected Order:=================", order);
        const accountMove = order?.raw?.account_move;
        console.log("Account Move ID:==============", accountMove);
            try {
                    console.log("Calling API to create copy invoice for move ID:", accountMove);
                    const result = await rpc("/pos/create_copy_invoice", { move_id: accountMove });
                    console.log("Invoice copied. New Invoice Number:", result["Invoice Number"]);
                    this.pos.printReceipt({ order: order });
                } catch (error) {
                    console.error("Error during RPC call:", error);
                    if (error?.message) {
                        console.error("Server error:", error.message);
                    }
                }
        console.log("End of onClickPopup");
        console.log("print error==================");
    }
});