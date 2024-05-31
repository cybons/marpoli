function notifyDailyAssignee() {
  const sheetName = "当月シート"; // 月毎のシート名
  const masterSheetName = "マスタシート"; // マスタシート名
  const dateColumn = "C";
  const nameColumn = "D";
  const startRow = 3; // 開始行
  const today = new Date();
  const formattedToday = Utilities.formatDate(
    today,
    Session.getScriptTimeZone(),
    "yyyy/MM/dd"
  ); // 日付のフォーマット調整

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  const range = sheet.getRange(`${dateColumn}${startRow}:${dateColumn}`);
  const values = range.getValues();

  let assigneeName = null;

  for (let i = 0; i < values.length; i++) {
    if (values[i][0] === formattedToday) {
      assigneeName = sheet.getRange(`${nameColumn}${startRow + i}`).getValue();
      break;
    }
  }

  if (assigneeName) {
    const masterSheet =
      SpreadsheetApp.getActiveSpreadsheet().getSheetByName(masterSheetName);
    const masterValues = masterSheet.getDataRange().getValues();
    let slackUserId = null;

    for (let j = 0; j < masterValues.length; j++) {
      if (masterValues[j][0] === assigneeName) {
        slackUserId = masterValues[j][1];
        break;
      }
    }

    if (slackUserId) {
      const slackWebhookUrl =
        "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"; // Slack Webhook URL
      const payload = {
        text: `<@${slackUserId}> 今日の担当者です。`,
      };
      const options = {
        method: "post",
        contentType: "application/json",
        payload: JSON.stringify(payload),
      };

      UrlFetchApp.fetch(slackWebhookUrl, options);
    } else {
      Logger.log("担当者のSlack IDが見つかりません。");
    }
  } else {
    Logger.log("今日の日付に一致する担当者が見つかりません。");
  }
}
