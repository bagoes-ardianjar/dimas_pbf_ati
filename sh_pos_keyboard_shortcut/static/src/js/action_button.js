odoo.define("sh_pos_keyboard_shortcut.ActionButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");

    class ShortcutListTips extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-shortcut-tips", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
            let { confirmed, payload } = this.showPopup("ShortcutTipsPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
    }
    ShortcutListTips.template = "ShortcutListTips";
    ProductScreen.addControlButton({
        component: ShortcutListTips,
        condition: function () {
            return this.env.pos.config.sh_enable_shortcut;
        },
    });
    Registries.Component.add(ShortcutListTips);

    return {
        ShortcutListTips,
    };
});
