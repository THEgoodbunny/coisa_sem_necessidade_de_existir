/* churn-card.js */
(function () {
    function clamp(value, min, max) {
        const n = Number(value);

        if (!Number.isFinite(n)) return min;

        return Math.min(max, Math.max(min, n));
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function formatInt(value) {
        const n = Number(value);

        if (!Number.isFinite(n)) return "n/d";

        return Math.round(n).toLocaleString("pt-BR");
    }

    function formatPct(value) {
        const n = Number(value);

        if (!Number.isFinite(n)) return "n/d";

        return `${(n * 100).toFixed(1).replace(".", ",")}%`;
    }

    function makeUid(container) {
        if (container.id) return container.id;

        const suffix = Math.random().toString(16).slice(2, 10);
        container.id = `churn_${suffix}`;

        return container.id;
    }

    function getContainer(containerOrSelector) {
        if (typeof containerOrSelector === "string") {
            return document.querySelector(containerOrSelector);
        }

        return containerOrSelector;
    }

    function setupTooltip(card, uid, content) {
        document.querySelectorAll(`.ca-floating-tooltip[data-ca-owner="${uid}"]`).forEach((oldTooltip) => {
            oldTooltip.remove();
        });

        const tooltip = document.createElement("div");
        tooltip.className = "ca-floating-tooltip";
        tooltip.dataset.caOwner = uid;
        document.body.appendChild(tooltip);

        function moveTooltip(event) {
            const tooltipWidth = tooltip.offsetWidth || 390;
            const tooltipHeight = tooltip.offsetHeight || 520;
            const margin = 18;

            let x = event.clientX + margin;
            let y = event.clientY + margin;

            if (x + tooltipWidth > window.innerWidth - margin) {
                x = event.clientX - tooltipWidth - margin;
            }

            if (y + tooltipHeight > window.innerHeight - margin) {
                y = window.innerHeight - tooltipHeight - margin;
            }

            if (y < margin) y = margin;
            if (x < margin) x = margin;

            tooltip.style.left = `${x}px`;
            tooltip.style.top = `${y}px`;
        }

        function resetAutoScroll() {
            const inner = tooltip.querySelector(".ca-tooltip-inner");

            if (!inner) return;

            inner.classList.remove("ca-autoscroll");
            inner.style.removeProperty("--ca-scroll-distance");
            inner.style.removeProperty("animation-duration");
        }

        function applyAutoScroll() {
            const inner = tooltip.querySelector(".ca-tooltip-inner");

            if (!inner) return;

            resetAutoScroll();

            const availableHeight = tooltip.clientHeight;
            const contentHeight = inner.scrollHeight;
            const overflow = contentHeight - availableHeight;

            if (overflow > 8) {
                const distance = -(overflow + 14);
                const duration = Math.max(5, Math.min(16, overflow / 22));

                inner.style.setProperty("--ca-scroll-distance", `${distance}px`);
                inner.style.animationDuration = `${duration}s`;
                inner.classList.add("ca-autoscroll");
            }
        }

        function showTooltip(event) {
            const key = event.currentTarget.dataset.caKey;

            if (!key || !content[key]) return;

            tooltip.innerHTML = `<div class="ca-tooltip-inner">${content[key]}</div>`;
            tooltip.classList.add("is-visible");

            requestAnimationFrame(() => {
                applyAutoScroll();
                moveTooltip(event);
            });
        }

        function hideTooltip() {
            tooltip.classList.remove("is-visible");
            resetAutoScroll();
        }

        card.querySelectorAll(".ca-hoverable[data-ca-key]").forEach((el) => {
            el.addEventListener("mouseenter", showTooltip);
            el.addEventListener("mousemove", moveTooltip);
            el.addEventListener("mouseleave", hideTooltip);
        });
    }

    function render(containerOrSelector, payload) {
        const container = getContainer(containerOrSelector);

        if (!container) return;

        const data = payload || {};
        const uid = makeUid(container);

        const total = Number(data.total) || 0;
        const churnYes = Number(data.churn_yes) || 0;
        const retained = Number(data.retained) || Math.max(total - churnYes, 0);

        const churnRate = clamp(
            data.churn_rate ?? (total ? churnYes / total : 0),
            0,
            1
        );

        const retentionRate = clamp(
            data.retention_rate ?? (total ? retained / total : 0),
            0,
            1
        );

        const r = 86;
        const circ = 2 * Math.PI * r;
        const gapPx = 7;

        const retainedDash = Math.max(circ * retentionRate - gapPx, 0);
        const churnDash = Math.max(circ * churnRate - gapPx, 0);

        const retainedGap = circ - retainedDash;
        const churnGap = circ - churnDash;

        const startOffset = circ * 0.25;
        const churnOffset = startOffset - retainedDash - gapPx;

        const title = escapeHtml(data.title || "Visão geral de clientes");
        const eyebrow = escapeHtml(data.eyebrow || "Churn Analytics");
        const badgeLabel = escapeHtml(data.badge_label || "Base geral");

        const churnRateLabel = data.churn_rate_label || formatPct(churnRate);
        const retentionRateLabel = data.retention_rate_label || formatPct(retentionRate);
        const churnLabel = data.churn_label || formatInt(churnYes);
        const retainedLabel = data.retained_label || formatInt(retained);
        const totalLabel = data.total_label || formatInt(total);

        const retainedGradientId = `${uid}_retainedGradient`;
        const churnGradientId = `${uid}_churnGradient`;
        const softGlowId = `${uid}_softGlow`;
        const hotGlowId = `${uid}_hotGlow`;

        container.innerHTML = `
            <div class="ca-card" data-ca-id="${escapeHtml(uid)}"
                 style="--ca-circ:${circ}; --ca-churn-dash:${churnDash}; --ca-churn-gap:${churnGap};">
                <div class="ca-header">
                    <div>
                        <div class="ca-eyebrow">${eyebrow}</div>
                        <div class="ca-title">${title}</div>
                    </div>

                    <div class="ca-badge ca-overall-badge ca-hoverable" data-ca-key="overall">
                        ${badgeLabel}
                    </div>
                </div>

                <div class="ca-content">
                    <div class="ca-ring-wrap">
                        <svg width="250" height="250" viewBox="0 0 240 240" role="img" aria-label="Churn rate ${escapeHtml(churnRateLabel)}">
                            <defs>
                                <linearGradient id="${retainedGradientId}" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stop-color="#5eead4"/>
                                    <stop offset="100%" stop-color="#14b8a6"/>
                                </linearGradient>

                                <linearGradient id="${churnGradientId}" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stop-color="#fb7185"/>
                                    <stop offset="55%" stop-color="#f43f5e"/>
                                    <stop offset="100%" stop-color="#e11d48"/>
                                </linearGradient>

                                <filter id="${softGlowId}">
                                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                                    <feMerge>
                                        <feMergeNode in="coloredBlur"/>
                                        <feMergeNode in="SourceGraphic"/>
                                    </feMerge>
                                </filter>

                                <filter id="${hotGlowId}">
                                    <feGaussianBlur stdDeviation="5" result="coloredBlur"/>
                                    <feMerge>
                                        <feMergeNode in="coloredBlur"/>
                                        <feMergeNode in="SourceGraphic"/>
                                    </feMerge>
                                </filter>
                            </defs>

                            <circle
                                cx="120" cy="120" r="${r}"
                                fill="none"
                                stroke="rgba(148,163,184,.10)"
                                stroke-width="30"
                            />

                            <circle
                                class="ca-ring-segment ca-ring-retained ca-hoverable"
                                data-ca-key="retained"
                                cx="120" cy="120" r="${r}"
                                fill="none"
                                stroke="url(#${retainedGradientId})"
                                stroke-width="24"
                                stroke-linecap="round"
                                stroke-dasharray="${retainedDash} ${retainedGap}"
                                stroke-dashoffset="${startOffset}"
                                filter="url(#${softGlowId})"
                            />

                            <circle
                                class="ca-ring-segment ca-ring-churn ca-hoverable"
                                data-ca-key="churn"
                                cx="120" cy="120" r="${r}"
                                fill="none"
                                stroke="url(#${churnGradientId})"
                                stroke-width="28"
                                stroke-linecap="round"
                                stroke-dasharray="${churnDash} ${churnGap}"
                                stroke-dashoffset="${churnOffset}"
                                filter="url(#${hotGlowId})"
                            />
                        </svg>

                        <div class="ca-center-text">
                            <div class="ca-center-label">Churn rate</div>
                            <div class="ca-center-value">${escapeHtml(churnRateLabel)}</div>
                            <div class="ca-center-subtitle">${escapeHtml(churnLabel)} de ${escapeHtml(totalLabel)} clientes</div>
                        </div>
                    </div>

                    <div class="ca-metrics">
                        <div class="ca-metric-card ca-retained-card ca-hoverable" data-ca-key="retained">
                            <div class="ca-metric-label">Retidos</div>
                            <div class="ca-metric-value ca-retained-value">${escapeHtml(retainedLabel)}</div>
                            <div class="ca-metric-subtitle">${escapeHtml(retentionRateLabel)} da base</div>
                        </div>

                        <div class="ca-metric-card ca-churn-card-small ca-hoverable" data-ca-key="churn">
                            <div class="ca-metric-label">Churn</div>
                            <div class="ca-metric-value ca-churn-value">${escapeHtml(churnLabel)}</div>
                            <div class="ca-metric-subtitle">${escapeHtml(churnRateLabel)} da base</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const card = container.querySelector(".ca-card");
        setupTooltip(card, uid, data.tooltip || {});
    }

    window.ChurnCard = {
        render
    };
})();
