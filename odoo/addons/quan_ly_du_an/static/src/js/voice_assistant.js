odoo.define('quan_ly_du_an.voice_assistant', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var rpc = require('web.rpc');

$(document).ready(function() {
    $(document).on('click', '.btn-voice-command', function(e) {
        e.preventDefault();
        
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            Dialog.alert(this, "Trình duyệt của bạn không hỗ trợ nhận diện giọng nói (Web Speech API). Vui lòng sử dụng Google Chrome, Edge hoặc Safari bản mới nhất.");
            return;
        }

        var recognition = new SpeechRecognition();
        recognition.lang = 'vi-VN';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        // UI Overlay for recording
        var $indicator = $('<div id="voice-recording-indicator" style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); background:rgba(0,0,0,0.85); color:white; padding:30px; border-radius:15px; z-index:9999; text-align:center; box-shadow:0 0 20px rgba(243,156,18,0.8); width: 400px; max-width: 90%;"><i class="fa fa-microphone fa-3x fa-pulse" style="color:#f39c12; margin-bottom:15px;"></i><h3 style="margin-top:0; color: white;">Đang lắng nghe...</h3><p style="color: #ccc; font-size: 14px;">Hãy đọc lệnh của bạn.<br/><i>(VD: "Cập nhật ngân sách thành năm mươi triệu" hoặc "Chuyển sang trạng thái triển khai")</i></p></div>');
        
        if ($('#voice-recording-indicator').length === 0) {
            $('body').append($indicator);
        }

        recognition.start();

        recognition.onresult = function(event) {
            var speechResult = event.results[0][0].transcript;
            console.log('Voice recognized:', speechResult);
            
            // Switch UI to processing mode
            $('#voice-recording-indicator').html('<i class="fa fa-cogs fa-3x fa-spin" style="color:#00a65a; margin-bottom:15px;"></i><h3 style="margin-top:0; color: white;">AI đang phân tích...</h3><p style="color: #ccc; font-size: 14px;">"' + speechResult + '"</p>');
            
            // Get current active record ID from URL hash
            var urlParams = new URLSearchParams(window.location.hash.substring(1));
            var projectIdStr = urlParams.get('id');
            var projectId = parseInt(projectIdStr);
            
            if (!projectId || isNaN(projectId)) {
                // If ID is not in hash (e.g. form opened directly or new record), we could try reading the URL or the DOM, but typically id is in the hash in Odoo
                // For safety, warn user
                $('#voice-recording-indicator').remove();
                Dialog.alert(this, "Tính năng giọng nói chỉ khả dụng khi đang mở chi tiết một Dự án đã lưu.");
                return;
            }

            // Call Backend Python Model
            rpc.query({
                model: 'quan_ly.du_an',
                method: 'process_voice_command',
                args: [[projectId], speechResult],
            }).then(function(result) {
                $('#voice-recording-indicator').remove();
                if (result && result.success) {
                    // Triggers a full reload to show updated fields. 
                    window.location.reload(); 
                } else {
                    Dialog.alert(this, "AI: " + (result.error || "Không thể thực thi lệnh. Vui lòng nói rõ hơn."));
                }
            }).catch(function(err) {
                $('#voice-recording-indicator').remove();
                console.error(err);
                Dialog.alert(this, "Lỗi kết nối RPC tới máy chủ.");
            });
        };

        recognition.onspeechend = function() {
            recognition.stop();
        };

        recognition.onerror = function(event) {
            $('#voice-recording-indicator').remove();
            console.error('Speech recognition error: ' + event.error);
            if (event.error !== 'no-speech') {
                Dialog.alert(this, "Lỗi Voice Recognition: " + event.error + ". Hãy đảm bảo bạn đã cấp quyền sử dụng Micro cho trang web.");
            }
        };
    });
});

});
