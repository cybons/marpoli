function syncTasksToCalendar() {
  const lock = LockService.getScriptLock();
  try {
    lock.tryLock(30000); // 最大30秒間ロックを待機
  } catch (e) {
    Logger.log('スクリプトが既に実行中です。');
    return;
  }

  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tasks');
    const logSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Logs');
    const data = sheet.getDataRange().getValues();
    const calendar = CalendarApp.getCalendarById('your_calendar_id@group.calendar.google.com');

    // タスクIDごとにデータをグループ化
    const tasks = {};
    data.slice(1).forEach((row, index) => {
      const [subject, dueDate, taskId, status, eventId] = row;
      if (!tasks[taskId]) {
        tasks[taskId] = [];
      }
      tasks[taskId].push({
        rowIndex: index + 2, // シートの行番号
        subject,
        dueDate,
        status,
        eventId
      });
    });

    const deleteRows = []; // 削除対象の行を収集

    for (const taskId in tasks) {
      const taskEntries = tasks[taskId];

      // イベントIDが存在するエントリをフィルタリング
      const existingEvents = taskEntries.filter(entry => entry.eventId);
      // イベントIDが存在しないエントリ
      const entriesWithoutEventId = taskEntries.filter(entry => !entry.eventId);

      // 最新のエントリを特定（スプレッドシートの下にあるものを最新と仮定）
      const latestEntry = taskEntries[taskEntries.length - 1];

      // `latestEntry` が「完了」の場合、関連イベントを削除
      if (latestEntry.status === '完了') {
        if (existingEvents.length > 0) {
          const latestEventEntry = existingEvents[existingEvents.length - 1];
          try {
            const event = calendar.getEventById(latestEventEntry.eventId);
            if (event) {
              event.deleteEvent();
              logOperation(logSheet, '削除', taskId, latestEventEntry.eventId);
            }
            // スプレッドシートのイベントIDをクリア
            sheet.getRange(latestEventEntry.rowIndex, 5).setValue('');
          } catch (error) {
            notifySlack(`タスクID: ${taskId} のカレンダー同期中にエラーが発生しました: ${error.message}`);
            logOperation(logSheet, 'エラー', taskId, latestEventEntry.eventId || '', error.message);
            continue; // 次のタスクへ
          }
        }

        // 完了したタスクの全行を削除対象に追加
        taskEntries.forEach(entry => {
          deleteRows.push(entry.rowIndex);
          logOperation(logSheet, '重複行削除', taskId, entry.eventId || '');
        });
        continue; // 次のタスクへ
      }

      // `latestEntry` が「完了」でない場合の処理
      try {
        if (existingEvents.length > 0) {
          // 既存のイベントがある場合、最新のエントリを更新
          const latestEventEntry = existingEvents[existingEvents.length - 1];
          const eventId = latestEventEntry.eventId;
          const event = calendar.getEventById(eventId);
          if (event) {
            const newDueDate = latestEntry.dueDate ? new Date(latestEntry.dueDate) : getOneWeekLater();
            if (latestEntry.dueDate) {
              event.setAllDayDate(newDueDate);
            } else {
              // 終日予定でない場合、特定の時間を設定
              const startTime = new Date(newDueDate);
              startTime.setHours(15, 0);
              const endTime = new Date(newDueDate);
              endTime.setHours(16, 0);
              event.setTime(startTime, endTime);
            }
            // 通知設定の更新
            event.setNotifications([
              { method: 'popup', minutes: 1440 }, // 1日前
              { method: 'popup', minutes: 4320 }, // 3日前
            ]);
            logOperation(logSheet, '更新', taskId, eventId);

            // イベントIDをスプレッドシートに再設定（念のため）
            sheet.getRange(latestEventEntry.rowIndex, 5).setValue(event.getId());
          }
        } else {
          // 新規イベントの登録
          const eventDate = latestEntry.dueDate ? new Date(latestEntry.dueDate) : getOneWeekLater();
          let event;
          if (latestEntry.dueDate) {
            // 完了予定日がある場合は終日イベントとして登録
            event = calendar.createAllDayEvent(latestEntry.subject, eventDate, {
              description: `タスクID: ${taskId}`,
            });
          } else {
            // 完了予定日がない場合は特定の時間を設定
            const startTime = new Date(eventDate);
            startTime.setHours(15, 0);
            const endTime = new Date(eventDate);
            endTime.setHours(16, 0);
            event = calendar.createEvent(latestEntry.subject, startTime, endTime, {
              description: `タスクID: ${taskId}`,
            });
          }

          // 通知設定の追加
          event.setNotifications([
            { method: 'popup', minutes: 1440 }, // 1日前
            { method: 'popup', minutes: 4320 }, // 3日前
          ]);

          // イベントIDをスプレッドシートに記載
          sheet.getRange(latestEntry.rowIndex, 5).setValue(event.getId());
          logOperation(logSheet, '登録', taskId, event.getId());
        }

        // 既存のイベントがあり、最新エントリが更新された場合、古いイベントを削除
        if (existingEvents.length > 1) {
          for (let i = 0; i < existingEvents.length - 1; i++) {
            const oldEventEntry = existingEvents[i];
            const oldEventId = oldEventEntry.eventId;
            try {
              const oldEvent = calendar.getEventById(oldEventId);
              if (oldEvent) {
                oldEvent.deleteEvent();
                logOperation(logSheet, '古いイベント削除', taskId, oldEventId);
              }
              // スプレッドシートのイベントIDをクリア
              sheet.getRange(oldEventEntry.rowIndex, 5).setValue('');
            } catch (error) {
              notifySlack(`タスクID: ${taskId} の古いイベント削除中にエラーが発生しました: ${error.message}`);
              logOperation(logSheet, 'エラー', taskId, oldEventId || '', error.message);
            }
          }
        }

        // イベントIDがないエントリを削除（最新のエントリにイベントIDが追加されている場合）
        entriesWithoutEventId.forEach(entry => {
          if (entry.rowIndex !== latestEntry.rowIndex) {
            deleteRows.push(entry.rowIndex);
            logOperation(logSheet, '重複行削除', taskId, entry.eventId || '');
          }
        });

      } catch (error) {
        notifySlack(`タスクID: ${taskId} のカレンダー同期中にエラーが発生しました: ${error.message}`);
        logOperation(logSheet, 'エラー', taskId, latestEntry.eventId || '', error.message);
      }
    }

    // 削除対象の行を一括で削除（行インデックスがずれないように降順で削除）
    deleteRows.sort((a, b) => b - a).forEach(row => {
      sheet.deleteRow(row);
    });

  } finally {
    lock.releaseLock();
  }
}

function getOneWeekLater() {
  const date = new Date();
  date.setDate(date.getDate() + 7);
  return date;
}

function notifySlack(message) {
  const webhookUrl = 'https://hooks.slack.com/services/your/webhook/url';
  const payload = JSON.stringify({ text: message });
  UrlFetchApp.fetch(webhookUrl, {
    method: 'post',
    contentType: 'application/json',
    payload: payload,
  });
}

function logOperation(logSheet, operation, taskId, eventId, error = '') {
  logSheet.appendRow([new Date(), operation, taskId, eventId, error]);
}
