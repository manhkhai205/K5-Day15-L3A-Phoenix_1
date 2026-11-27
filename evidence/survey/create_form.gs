/**
 * Tạo Google Form khảo sát theo evidence/survey/questions.md — nhóm Phoenix_1 (Track C1).
 *
 * Cách chạy (≈2 phút):
 *   1. Mở https://script.google.com → New project.
 *   2. Xoá code mẫu, dán toàn bộ file này vào → Save.
 *   3. Chọn hàm createSurveyForm → Run → cấp quyền (Google Forms + Sheets) cho tài khoản của bạn.
 *   4. Xem View → Logs (hoặc Execution log): có link điền form (gửi đi) và link sửa form.
 *
 * Form không thu email, không hỏi tên/SĐT. Câu 1 trả lời "Chưa" → nộp luôn (lọc sai đối tượng).
 * Câu trả lời tự đổ vào một Google Sheet → File → Download → CSV, xoá cột liên hệ trước khi commit.
 */
function createSurveyForm() {
  var form = FormApp.create('Khảo sát: Đưa bé đi công viên chủ đề — lần gần nhất của bạn');
  form.setDescription(
    'Nhóm sinh viên đang tìm hiểu cách các gia đình lên kế hoạch đi chơi công viên chủ đề ' +
    '(VinWonders, Sun World, Đầm Sen…). Khoảng 3 phút, không hỏi tên, email hay số điện thoại. ' +
    'Các câu hỏi về LẦN GẦN NHẤT bạn đi — không có đúng/sai. Cảm ơn bạn!'
  );
  form.setCollectEmail(false);
  form.setProgressBar(true);
  form.setConfirmationMessage('Cảm ơn bạn đã chia sẻ! Câu trả lời giúp nhóm hiểu đúng khó khăn của các gia đình.');
  try { form.setRequireLogin(false); } catch (e) { /* chỉ có ở tài khoản Workspace */ }

  // Câu 1 — sàng lọc
  var q1 = form.addMultipleChoiceItem()
    .setTitle('1. Trong 12 tháng qua, bạn đã đi công viên chủ đề lớn (VinWonders, Sun World, Đầm Sen, Suối Tiên…) cùng trẻ dưới 12 tuổi chưa?')
    .setRequired(true);
  q1.setChoices([
    q1.createChoice('Có', FormApp.PageNavigationType.CONTINUE),
    q1.createChoice('Chưa', FormApp.PageNavigationType.SUBMIT)
  ]);

  form.addPageBreakItem().setTitle('Về lần gần nhất bạn đi');

  // Câu 2
  form.addMultipleChoiceItem()
    .setTitle('2. Lần gần nhất là ở đâu?')
    .setChoiceValues(['VinWonders Phú Quốc', 'VinWonders khác (Nha Trang, Nam Hội An…)', 'Sun World'])
    .showOtherOption(true)
    .setRequired(true);

  // Câu 3 — hai ô số
  var numberRule = FormApp.createTextValidation()
    .requireWholeNumber()
    .setHelpText('Nhập một số nguyên, vd 2')
    .build();
  form.addTextItem()
    .setTitle('3a. Lần đó nhóm bạn có mấy người lớn?')
    .setValidation(numberRule)
    .setRequired(true);
  form.addTextItem()
    .setTitle('3b. Có mấy trẻ cao dưới 1,4m?')
    .setValidation(numberRule)
    .setRequired(true);

  // Câu 4
  form.addCheckboxItem()
    .setTitle('4. Trước hôm đó, bạn chuẩn bị lịch chơi bằng cách nào? (chọn nhiều)')
    .setChoiceValues([
      'Đọc blog / review',
      'Hỏi trong hội nhóm (Facebook, Zalo…)',
      'App của công viên',
      'ChatGPT / công cụ AI',
      'Hỏi người quen',
      'Không chuẩn bị'
    ])
    .showOtherOption(true)
    .setRequired(true);

  // Câu 5
  form.addMultipleChoiceItem()
    .setTitle('5. Việc chuẩn bị lịch đó mất khoảng bao lâu?')
    .setChoiceValues(['Dưới 15 phút', '15–30 phút', '30–60 phút', 'Trên 60 phút', 'Không chuẩn bị'])
    .setRequired(true);

  // Câu 6
  form.addCheckboxItem()
    .setTitle('6. Trong ngày hôm đó, chuyện nào ĐÃ XẢY RA? (chọn nhiều)')
    .setChoiceValues([
      'Lỡ show muốn xem',
      'Đi vòng / quay lại khu đã đi qua',
      'Bé không đủ chiều cao chơi trò đã định',
      'Mưa / nắng làm phải đổi lịch',
      'Khu hoặc trò đóng cửa / bảo trì',
      'Chi tiêu vượt dự tính',
      'Không có chuyện nào kể trên'
    ])
    .setRequired(true);

  // Câu 7
  form.addMultipleChoiceItem()
    .setTitle('7. Khi kế hoạch bị vỡ, bạn mất khoảng bao lâu để quyết lại nên đi đâu tiếp?')
    .setChoiceValues(['Kế hoạch không bị vỡ', 'Dưới 5 phút', '5–15 phút', '15–30 phút', 'Trên 30 phút'])
    .setRequired(true);

  // Câu 8
  form.addMultipleChoiceItem()
    .setTitle('8. Tổng chi hôm đó so với dự tính trước?')
    .setChoiceValues(['Thấp hơn', 'Gần bằng', 'Vượt dưới 20%', 'Vượt trên 20%', 'Không dự tính trước'])
    .setRequired(true);

  // Câu 9
  form.addParagraphTextItem()
    .setTitle('9. Điều gì khó chịu nhất trong ngày hôm đó? Kể cụ thể giúp nhóm nhé.')
    .setRequired(false);

  // Câu 10 — tuỳ chọn
  form.addMultipleChoiceItem()
    .setTitle('10. (Tuỳ chọn) Bạn có sẵn lòng cho nhóm hỏi thêm khoảng 10 phút không?')
    .setChoiceValues(['Có', 'Không'])
    .setRequired(false);
  form.addTextItem()
    .setTitle('Nếu có: cách liên hệ (không bắt buộc — Zalo / Facebook / email)')
    .setRequired(false);

  // Đổ câu trả lời vào Google Sheet để xuất CSV
  var sheet = SpreadsheetApp.create('Kết quả khảo sát — công viên chủ đề (Phoenix_1)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  Logger.log('Link điền form (gửi cho người khảo sát): ' + form.getPublishedUrl());
  Logger.log('Link sửa form: ' + form.getEditUrl());
  Logger.log('Sheet kết quả: ' + sheet.getUrl());
}
