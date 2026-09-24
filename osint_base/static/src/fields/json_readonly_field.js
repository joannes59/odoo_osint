/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

export class JsonReadonlyField extends Component {
    static template = "osint_base.JsonReadonlyField";
    static props = {
        ...Component.props,
        record: { type: Object },
        name: { type: String },
    };

    get value() {
        return this.props.record.data[this.props.name] || {};
    }

    get formattedJson() {
        try {
            return JSON.stringify(this.value, null, 4);
        } catch {
            return "";
        }
    }

    get isEmpty() {
        const val = this.value;
        return !val || (typeof val === "object" && Object.keys(val).length === 0);
    }
}

export const jsonReadonlyField = {
    component: JsonReadonlyField,
    displayName: "JSON (Read only)",
    supportedTypes: ["json"],
};

registry.category("fields").add("json_readonly", jsonReadonlyField);