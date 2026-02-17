import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

patch(PosOrder.prototype, {
    async export_for_printing(baseUrl, headerData) {
        const result = await super.export_for_printing(...arguments);
        const order = this;
        console.log(order,'================order')
        const accountMove = order?.raw?.account_move;
        console.log("Account Move ID:==============", accountMove);
        console.log("Calling API to create copy invoice for move ID:", accountMove);
        const result1 = await rpc("/pos/order_print_data", { move_id: accountMove });
        console.log("result11111111111=====================:", result1);
        result.vmsSeData = {
        posID:'Yes'
        };
        console.log("result00000000000=====================:", result);
        console.log("vmsSeData=====================:", result.vmsSeData);
        return result;
    },
});
