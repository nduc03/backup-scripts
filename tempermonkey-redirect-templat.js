// ==UserScript==
// @name         API Redirector
// @namespace    https://github.com/your-username/tampermonkey-scripts
// @version      1.0.0
// @description  Intercept and redirect API requests from remote environments (Dev/Staging/UAT) to local backend services while preserving HTTP method, headers, and payloads.
// @author       Antigravity
//
// =============================================================================
// BƯỚC 1: CẤU HÌNH DOMAIN ÁP DỤNG (METADATA MATCH/INCLUDE)
// Thay thế các mẫu dưới đây bằng domain trang web bạn muốn chạy script:
//
// Ví dụ:
// - Khớp 1 domain cụ thể:          *://dev.example.com/*
// - Khớp tất cả subdomain:          *://*.example.com/*
// - Khớp tiền tố (Dev/UAT/Staging): *://dev-*.example.com/* hoặc regex bên dưới
// =============================================================================
// @match        *://*.example.com/*
// @include      *://dev-*.example.com/*
// @include      *://uat-*.example.com/*
// @include      *://staging-*.example.com/*
// @include      /^https?:\/\/(dev|uat|staging)-[^\/]+\.example\.com\/.*$/
//
// =============================================================================
// CẤU HÌNH THỜI ĐIỂM CHẠY & QUYỀN TRUY CẬP
// Giữ nguyên @run-at document-start để can thiệp trước khi trang web gọi API.
// =============================================================================
// @run-at       document-start
// @grant        unsafeWindow
// ==/UserScript==

(function () {
    'use strict';

    /**
     * =========================================================================
     * BƯỚC 2: CẤU HÌNH BẢNG ÁNH XẠ URL (URL_MAPPINGS)
     * =========================================================================
     * Định nghĩa các cặp base URL cần chuyển hướng từ Remote về Localhost.
     * 
     * QUY TẮC:
     * - `from`: Base URL ban đầu của API remote (trang web đang gọi).
     * - `to`  : Base URL của backend chạy dưới máy local (thường là http://localhost:PORT/...).
     * 
     * Template để thêm cặp mới:
     * {
     *     from: 'https://[subdomain].[your-domain].com/[api-gateway-path]',
     *     to:   'http://localhost:[port]/[local-path]'
     * },
     */
    const URL_MAPPINGS = [
        // ---------------------------------------------------------------------
        // MẪU 1: Remote Gateway API -> Local Service 1
        // ---------------------------------------------------------------------
        {
            from: 'https://dev-api.example.com/gw/service-a/api',
            to:   'http://localhost:8080/api'
        },

        // ---------------------------------------------------------------------
        // MẪU 2: Remote Admin Service -> Local Service 2 (Khác Port)
        // ---------------------------------------------------------------------
        // {
        //     from: 'https://staging.example.com/api/admin',
        //     to:   'http://localhost:8181/api/admin'
        // },

        // ---------------------------------------------------------------------
        // MẪU 3: Remote Path tương đối hoặc API chung
        // ---------------------------------------------------------------------
        // {
        //     from: 'https://uat.example.com/api/v1',
        //     to:   'http://localhost:3000/api/v1'
        // },
    ];

    /**
     * Tùy chọn bật/tắt in log chuyển hướng trong F12 Console
     */
    const ENABLE_CONSOLE_LOG = true;

    // =========================================================================
    // CORE LOGIC (KHÔNG CẦN CHỈNH SỬA PHẦN NÀY)
    // =========================================================================
    const targetWin = typeof unsafeWindow !== 'undefined' ? unsafeWindow : window;

    /**
     * Phân tích và thay thế URL nếu khớp với rule trong URL_MAPPINGS
     */
    function rewriteUrl(rawUrl, method = 'REQUEST') {
        if (!rawUrl || typeof rawUrl !== 'string') return rawUrl;

        // Xử lý cả URL tuyệt đối và URL tương đối
        let absoluteUrl = rawUrl;
        try {
            absoluteUrl = new URL(rawUrl, targetWin.location.href).href;
        } catch (_) {}

        for (const rule of URL_MAPPINGS) {
            if (!rule.from || !rule.to) continue;

            const fromClean = rule.from.replace(/\/+$/, '');
            const toClean = rule.to.replace(/\/+$/, '');

            for (const candidate of [rawUrl, absoluteUrl]) {
                if (candidate === fromClean) {
                    logRedirect(method, rawUrl, toClean);
                    return toClean;
                }
                if (candidate.startsWith(fromClean + '/') || candidate.startsWith(fromClean + '?')) {
                    const rewritten = toClean + candidate.slice(fromClean.length);
                    logRedirect(method, rawUrl, rewritten);
                    return rewritten;
                }
            }
        }
        return rawUrl;
    }

    /**
     * In log ra F12 Console để dễ dàng theo dõi request
     */
    function logRedirect(method, from, to) {
        if (!ENABLE_CONSOLE_LOG) return;
        console.log(
            `%c[Dev Proxy %s]%c %s\n  ➔ %c%s`,
            'background: #2c3e50; color: #ecf0f1; font-weight: bold; padding: 2px 5px; border-radius: 3px;',
            method.toUpperCase(),
            'color: #e67e22; font-weight: bold;',
            from,
            'color: #27ae60; font-weight: bold;',
            to
        );
    }

    // -------------------------------------------------------------------------
    // 1. Hook window.fetch
    // -------------------------------------------------------------------------
    if (targetWin.fetch) {
        const originalFetch = targetWin.fetch;
        targetWin.fetch = function (input, init) {
            let method = (init && init.method) ? init.method : 'GET';

            if (typeof input === 'string') {
                input = rewriteUrl(input, method);
            } else if (input instanceof URL) {
                input = new URL(rewriteUrl(input.href, method));
            } else if (input instanceof Request) {
                method = input.method || method;
                const newUrl = rewriteUrl(input.url, method);
                if (newUrl !== input.url) {
                    input = new Request(newUrl, input);
                }
            }
            return originalFetch.apply(this, [input, init]);
        };
    }

    // -------------------------------------------------------------------------
    // 2. Hook window.XMLHttpRequest (jQuery $.ajax, Axios, raw XHR)
    // -------------------------------------------------------------------------
    if (targetWin.XMLHttpRequest) {
        const originalOpen = targetWin.XMLHttpRequest.prototype.open;
        targetWin.XMLHttpRequest.prototype.open = function (method, url, async, user, password) {
            const newUrl = rewriteUrl(url, method);
            return originalOpen.call(this, method, newUrl, async !== undefined ? async : true, user, password);
        };
    }

})();
