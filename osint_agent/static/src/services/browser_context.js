/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Thread } from "@mail/core/common/thread_model";
import { patch } from "@web/core/utils/patch";

const browserContextService = {
    dependencies: [],

    start() {
        function getCurrent() {
            return {
                pathname: window.location.pathname,
                search: window.location.search,
                hash: window.location.hash,
            };
        }

        return {
            getCurrent,
        };
    },
};

registry
    .category("services")
    .add("browser_context", browserContextService);

patch(Thread.prototype, {
    async post(body, postData = {}, extraData = {}) {
        const browserContext =
            this.store.env.services.browser_context.getCurrent();

        return super.post(body, postData, {
            ...extraData,
            context: {
                ...(extraData.context || {}),
                browser_context: browserContext,
            },
        });
    },
});