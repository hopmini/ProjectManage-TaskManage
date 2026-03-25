odoo.define('quan_ly_du_an.ai_chat_widget', function (require) {
"use strict";
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;

    $(document).ready(function() {
        if ($('#odoo-ai-chat-button').length > 0) return;

        // Create the floating button
        var $button = $('<div id="odoo-ai-chat-button" class="ai-floating-button">' +
            '<i class="fa fa-comments"></i>' +
            '</div>');
        
        // Create the chat window
        var $chatWindow = $('<div id="odoo-ai-chat-window" class="ai-chat-window" style="display:none;">' +
            '<div class="ai-chat-header">' +
                '<div class="ai-header-left">' +
                    '<div class="ai-status-dot"></div>' +
                    '<span>Trợ lý AI FitDnu</span>' +
                '</div>' +
                '<div class="ai-header-right">' +
                    '<i class="fa fa-minus ai-chat-minimize" title="Thu nhỏ"></i>' +
                '</div>' +
            '</div>' +
            '<div class="ai-chat-history">' +
                '<div class="ai-bubble ai"><div class="ai-bubble-content">Xin chào! Tôi là trợ lý ảo hỗ trợ quản lý dự án. Tôi có thể giúp gì cho bạn?</div></div>' +
            '</div>' +
            '<div class="ai-chat-quick-actions">' +
                '<button class="ai-quick-btn" data-msg="Tóm tắt tình hình các dự án">Tóm tắt dự án</button>' +
                '<button class="ai-quick-btn" data-msg="Danh sách dự án trễ hạn">Kiểm tra trễ hạn</button>' +
            '</div>' +
            '<div class="ai-chat-input-area">' +
                '<div class="ai-input-wrapper">' +
                    '<i class="fa fa-bars ai-chat-menu" title="Menu"></i>' +
                    '<input type="text" placeholder="Nhập tin nhắn..." class="ai-chat-input"/>' +
                    '<button class="ai-chat-send"><i class="fa fa-paper-plane"></i></button>' +
                '</div>' +
            '</div>' +
            '</div>');

        $('body').append($button).append($chatWindow);

        // Toggle chat window
        $button.click(function() {
            $chatWindow.fadeToggle(200);
            $(this).toggleClass('active');
        });

        // Minimize
        $('.ai-chat-minimize').click(function() {
            $chatWindow.fadeOut(200);
            $button.removeClass('active');
        });

        // Send message function
        function sendMessage(message) {
            if (!message || message.trim() === "") return;
            
            var $history = $('.ai-chat-history');
            $history.append('<div class="user-bubble"><div class="user-bubble-content">' + message + '</div></div>');
            $history.scrollTop($history[0].scrollHeight);
            $('.ai-chat-input').val('');

            // Add loading indicator
            var $loading = $('<div class="ai-bubble ai loading"><div class="ai-bubble-content">...</div></div>');
            $history.append($loading);
            $history.scrollTop($history[0].scrollHeight);

            // Call Odoo RPC
            rpc.query({
                model: 'quan_ly.ai_chat',
                method: 'action_send_message_from_widget',
                args: [message],
            }).then(function(result) {
                $loading.remove();
                if (result && result.response) {
                    var responseHtml = result.response.replace(/\n/g, '<br>');
                    $history.append('<div class="ai-bubble ai"><div class="ai-bubble-content">' + responseHtml + '</div></div>');
                } else {
                    $history.append('<div class="ai-bubble ai"><div class="ai-bubble-content">Rất tiếc, tôi không thể trả lời lúc này.</div></div>');
                }
                $history.scrollTop($history[0].scrollHeight);
            }).catch(function(err) {
                $loading.remove();
                $history.append('<div class="ai-bubble ai error"><div class="ai-bubble-content">Lỗi kết nối máy chủ.</div></div>');
                $history.scrollTop($history[0].scrollHeight);
            });
        }

        // Click send
        $('.ai-chat-send').click(function() {
            sendMessage($('.ai-chat-input').val());
        });

        // Press Enter
        $('.ai-chat-input').keypress(function(e) {
            if (e.which == 13) {
                sendMessage($(this).val());
            }
        });

        // Quick actions
        $('.ai-quick-btn').click(function() {
            sendMessage($(this).data('msg'));
        });

        // Menu actions
        $('.ai-chat-menu').click(function() {
            if (confirm("Xóa lịch sử trò chuyện?")) {
                rpc.query({
                   model: 'quan_ly.ai_chat',
                   method: 'action_clear_history',
                   args: [[]], // This will clear session history
                });
                $('.ai-chat-history').html('<div class="ai-bubble ai"><div class="ai-bubble-content">Lịch sử đã được xóa. Tôi có thể giúp gì thêm?</div></div>');
            }
        });
    });
});
