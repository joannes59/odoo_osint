/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

// ─── Utility helpers ───────────────────────────────────────────────────────

/**
 * Recursively build a normalised tree node from a JS value.
 */
function buildNode(value, key, id, depth = 0) {
    const type = Array.isArray(value) ? "array"
               : value === null      ? "null"
               : typeof value;

    const node = { id, key: String(key), type, depth };

    if (type === "object" || type === "array") {
        const entries = type === "array"
            ? value.map((v, i) => [i, v])
            : Object.entries(value);
        node.children = entries.map(([k, v], i) =>
            buildNode(v, k, `${id}_${i}`, depth + 1)
        );
        node.childCount = node.children.length;
        node.label = type === "array"
            ? `(${node.childCount} item${node.childCount !== 1 ? "s" : ""})`
            : `(${node.childCount} propert${node.childCount !== 1 ? "ies" : "y"})`;
    } else {
        node.value = value;
    }
    return node;
}

/**
 * Returns true if this node OR any of its descendants match the filter.
 */
function nodeMatchesFilter(node, filterLow) {
    if (!filterLow) return true;
    if (node.key.toLowerCase().includes(filterLow)) return true;
    if (node.type !== "object" && node.type !== "array" &&
        String(node.value ?? "").toLowerCase().includes(filterLow)) return true;
    if (node.children) {
        return node.children.some(child => nodeMatchesFilter(child, filterLow));
    }
    return false;
}

/**
 * Flatten the tree into a renderable list.
 * When a filter is active:
 *   - Nodes that don't match (and have no matching descendants) are hidden.
 *   - Parent nodes with matching children are always expanded.
 * @param {Array}  nodes        - root-level nodes
 * @param {Set}    collapsedIds - set of node ids that are collapsed (only used when no filter)
 * @param {string} filter       - optional text filter
 */
function flattenTree(nodes, collapsedIds, filter = "") {
    const rows = [];
    const filterLow = filter.trim().toLowerCase();
    const isFiltering = !!filterLow;

    function walk(nodeList) {
        for (const node of nodeList) {
            // Skip nodes that don't match at all when filtering
            if (isFiltering && !nodeMatchesFilter(node, filterLow)) continue;

            const ownMatch = !filterLow ||
                node.key.toLowerCase().includes(filterLow) ||
                (node.type !== "object" && node.type !== "array" &&
                 String(node.value ?? "").toLowerCase().includes(filterLow));

            // When filtering: force expand so matching children are visible
            // When not filtering: respect collapsedIds
            const isCollapsed = isFiltering ? false : collapsedIds.has(node.id);

            rows.push({ ...node, collapsed: isCollapsed, matchesFilter: ownMatch });

            if ((node.type === "object" || node.type === "array") &&
                !isCollapsed && node.children) {
                walk(node.children);
            }
        }
    }
    walk(nodes);
    return rows;
}

/**
 * Collect all ids of object/array nodes in the tree.
 */
function collectAllIds(nodes, out = []) {
    for (const n of nodes) {
        if (n.type === "object" || n.type === "array") {
            out.push(n.id);
            if (n.children) collectAllIds(n.children, out);
        }
    }
    return out;
}

// ─── Main Component ───────────────────────────────────────────────────────

export class DoJsonWidget extends Component {
    static template = "do_json_widget.DoJsonWidget";
    static props = {
        ...standardFieldProps,
        noEditJson: { type: Boolean, optional: true },
    };

    setup() {
        this.notification = useService("notification");

        // collapsedIds tracks which node ids are collapsed — kept outside reactive
        // state to avoid proxy-mutation issues; state.rows is rebuilt on each toggle.
        this._tree = [];           // raw (non-reactive) tree built from JSON
        this._collapsedIds = new Set();  // ids that are currently collapsed

        this.state = useState({
            rows: [],
            filter: "",
            showRaw: false,
            editMode: false,
            editText: "",
            editError: "",
            isValid: true,
            copyMsg: false,
        });

        this._buildTree(this._currentJson());

        onWillUpdateProps((nextProps) => {
            const nextVal = nextProps.record.data[nextProps.name];
            const curVal  = this.props.record.data[this.props.name];
            if (JSON.stringify(nextVal) !== JSON.stringify(curVal)) {
                this._buildTree(this._parseValue(nextVal));
            }
        });
    }

    // ── Helpers ───────────────────────────────────────────────────

    _parseValue(raw) {
        if (!raw) return {};
        if (typeof raw === "string") {
            try { return JSON.parse(raw); } catch { return {}; }
        }
        return raw;
    }

    _currentJson() {
        return this._parseValue(this.props.record.data[this.props.name]);
    }

    _buildTree(data) {
        try {
            const root = buildNode(data || {}, "__root__", "root", -1);
            this._tree = root.children || [];
            // Default: collapse depth > 0
            this._collapsedIds = new Set(
                collectAllIds(this._tree).filter(id => {
                    // find depth: ids look like "root_0_1_2" => depth = segments-1
                    const depth = id.split("_").length - 1;
                    return depth > 0;
                })
            );
            this.state.isValid = true;
            this._refresh();
        } catch (e) {
            this.state.isValid = false;
            this.state.rows = [];
        }
    }

    _refresh() {
        this.state.rows = flattenTree(this._tree, this._collapsedIds, this.state.filter);
    }

    // ── Toolbar ───────────────────────────────────────────────────

    onFilterInput(ev) {
        this.state.filter = ev.target.value;
        this._refresh();
    }

    expandAll() {
        this._collapsedIds.clear();
        this._refresh();
    }

    collapseAll() {
        this._collapsedIds = new Set(collectAllIds(this._tree));
        this._refresh();
    }

    async copyJson() {
        try {
            await navigator.clipboard.writeText(JSON.stringify(this._currentJson(), null, 4));
        } catch { /* ignore */ }
        this.state.copyMsg = true;
        setTimeout(() => { this.state.copyMsg = false; }, 1800);
    }

    toggleRaw() {
        this.state.showRaw = !this.state.showRaw;
        if (this.state.showRaw) this.state.editMode = false;
    }

    toggleEdit() {
        // Edit is disabled if: readonly attr OR no_edit_json option is set
        if (this.props.readonly || this.props.noEditJson) return;
        this.state.editMode = !this.state.editMode;
        if (this.state.editMode) {
            this.state.showRaw = false;
            this.state.editText = JSON.stringify(this._currentJson(), null, 4);
            this.state.editError = "";
        }
    }

    // ── Tree toggle ───────────────────────────────────────────────

    toggleNode(id) {
        if (this._collapsedIds.has(id)) {
            this._collapsedIds.delete(id);
        } else {
            this._collapsedIds.add(id);
        }
        this._refresh();
    }

    // ── Edit mode ─────────────────────────────────────────────────

    onEditInput(ev) {
        this.state.editText = ev.target.value;
        this.state.editError = "";
        try {
            JSON.parse(ev.target.value);
            this.state.isValid = true;
        } catch (e) {
            this.state.isValid = false;
            this.state.editError = e.message;
        }
    }

    async applyEdit() {
        try {
            const parsed = JSON.parse(this.state.editText);
            await this.props.record.update({ [this.props.name]: parsed });
            this.state.editMode = false;
            this.state.editError = "";
            this.state.isValid = true;
            this._buildTree(parsed);
        } catch (e) {
            this.state.editError = _t("Invalid JSON: ") + e.message;
            this.state.isValid = false;
        }
    }

    cancelEdit() {
        this.state.editMode = false;
        this.state.editError = "";
        this.state.isValid = true;
        this._buildTree(this._currentJson());
    }

    // ── Template helpers ──────────────────────────────────────────

    get rawText() {
        return JSON.stringify(this._currentJson(), null, 4);
    }

    get isEmpty() {
        return !this._tree || this._tree.length === 0;
    }

    valueClass(row) {
        if (row.type === "null")    return "do_json_val_null";
        if (row.type === "boolean") return "do_json_val_bool";
        if (row.type === "number")  return "do_json_val_num";
        return "do_json_val_str";
    }

    valueLabel(row) {
        if (row.type === "null")   return "null";
        if (row.type === "string") return `"${row.value}"`;
        return String(row.value ?? "");
    }

    indentStyle(depth) {
        return `padding-left: ${Math.max(0, depth + 1) * 18}px`;
    }
}

export const doJsonField = {
    component: DoJsonWidget,
    displayName: _t("JSON Tree Viewer"),
    supportedTypes: ["json", "text", "char"],
    extractProps: ({ attrs, options }) => ({
        readonly: !!attrs.readonly,
        noEditJson: !!(options && options.no_edit_json),
    }),
};

registry.category("fields").add("do_json", doJsonField);
