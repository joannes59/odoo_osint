/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { loadJS } from "@web/core/assets";
import { Component, useRef, onWillStart, onMounted, onWillUpdateProps, useState } from "@odoo/owl";

let mermaidLoadPromise = null;
let mermaidIdCounter = 0;

function loadMermaid() {
    if (!mermaidLoadPromise) {
        mermaidLoadPromise = loadJS("/osint_base/static/lib/mermaid/mermaid.min.js").then(() => {
            window.mermaid.initialize({
                startOnLoad: false,
                theme: "default",
                securityLevel: "strict",
            });
        });
    }
    return mermaidLoadPromise;
}

export class MermaidField extends Component {
    static template = "osint_base.MermaidField";
    static props = { ...standardFieldProps };

    setup() {
        this.containerRef = useRef("container");
        this.state = useState({ error: null });
        this.diagramId = `mermaid-${++mermaidIdCounter}`;

        onWillStart(() => loadMermaid());
        onMounted(() => this.renderDiagram());
        onWillUpdateProps((nextProps) => {
            const newValue = nextProps.record.data[nextProps.name];
            const oldValue = this.props.record.data[this.props.name];
            if (newValue !== oldValue) {
                this.renderDiagram(newValue);
            }
        });
    }

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    async renderDiagram(source = this.value) {
        this.state.error = null;
        if (!this.containerRef.el) {
            return;
        }
        if (!source || !source.trim()) {
            this.containerRef.el.innerHTML = "";
            return;
        }
        try {
            await loadMermaid();
            const { svg } = await window.mermaid.render(this.diagramId + "-svg", source);
            if (this.containerRef.el) {
                this.containerRef.el.innerHTML = svg;
            }
        } catch (error) {
            this.state.error = error.message || String(error);
            if (this.containerRef.el) {
                this.containerRef.el.innerHTML = "";
            }
        }
    }
}

export const mermaidField = {
    component: MermaidField,
    displayName: "Diagramme Mermaid",
    supportedTypes: ["text", "html"],
};

registry.category("fields").add("mermaid", mermaidField);