odoo.define("sh_pos_keyboard_shortcut.Popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class ShortcutTipsPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
    }

    ShortcutTipsPopupWidget.template = "ShortcutTipsPopupWidget";
    Registries.Component.add(ShortcutTipsPopupWidget);

    return {
        ShortcutTipsPopupWidget,
    };
});
