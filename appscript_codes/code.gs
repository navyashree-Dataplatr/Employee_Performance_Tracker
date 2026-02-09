
// ======================================================================
// PROJECT: GOOGLE APPS SCRIPT - DAILY STATUS REPORT COLLECTOR
// TYPE: Container-Bound Script (attached to a Google Sheet)
// PURPOSE:
//   - Display a form (Frontend is HTML)
//   - Collect responses (Name, Tasks, Hours, etc.)
//   - Store submissions in a structured spreadsheet
//   - Auto-format rows for readability
// ======================================================================

// Name of the sheet where all submissions will be stored.
// If this sheet doesn't exist, the script will automatically create it.
const SHEET_NAME = "daily_reports_v2";


/**
 * ===========================
 * FUNCTION: doGet()
 * ===========================
 * PURPOSE:
 * - Runs whenever someone opens the Web App URL.
 * - Loads and displays the Form.html file to the user.
 * 
 * RETURNS:
 * - HTML output that renders the form UI.
 */
function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('Form') // Load Form.html file
    .setTitle('Daily Status Report')                  // Shown in browser tab title
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL); 
    // Allows embedding inside Google Chat messages or in iframe containers
}


/**
 * ===========================
 * FUNCTION: getSpreadsheet()
 * ===========================
 * PURPOSE:
 * - Returns the active Google spreadsheet.
 * - Since this script is bound to the sheet, no ID or file lookup is needed.
 */
function getSpreadsheet() {
  return SpreadsheetApp.getActiveSpreadsheet();
}


/**
 * ===========================
 * FUNCTION: saveToSheet(data)
 * ===========================
 * PURPOSE:
 * - Receives data submitted from the HTML form.
 * - Converts the data into a single formatted row.
 * - Appends it into the sheet defined in SHEET_NAME.
 * - If the sheet does NOT exist, it creates and formats it automatically.
 * 
 * PARAMETERS:
 * - data (object) containing submitted form details:
 *      { employeeName, email, reportDate, tasks:[{category,description,hours}], totalHours }
 * 
 * RETURNS:
 * - JSON object confirming success or reporting an error.
 */
function saveToSheet(data) {
  try {
    // Access the spreadsheet and sheet by name
    const ss = getSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);

    // ==========================================
    // CREATE SHEET ONLY IF IT DOES NOT EXIST
    // ==========================================
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAME); // Creates new sheet

      // Insert header row for data structure - MUST MATCH PYTHON CODE COLUMNS
      sheet.appendRow([
        "Timestamp",
        "Email_Address",
        "Name",
        "Date",
        "Tasks_Completed",
        "Time_Spent"
      ]);

      // Format header for better readability and UI presentation
      const headerRange = sheet.getRange(1, 1, 1, 6);
      headerRange.setFontWeight("bold");               // Make header text bold
      headerRange.setFontSize(11);                     // Standard readable size
      headerRange.setBackground("#4285f4");            // Google Blue header style
      headerRange.setFontColor("#ffffff");             // White text on blue
      headerRange.setHorizontalAlignment("center");     // Center aligned text
      headerRange.setVerticalAlignment("middle");       // Center text vertically
      headerRange.setBorder(true, true, true, true, true, true, "#ffffff", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

      // Set readable column widths (avoids squeezed columns)
      sheet.setColumnWidth(1, 180); // Timestamp
      sheet.setColumnWidth(2, 200); // Email_Address
      sheet.setColumnWidth(3, 150); // Name
      sheet.setColumnWidth(4, 100); // Date
      sheet.setColumnWidth(5, 500); // Tasks_Completed (big text area)
      sheet.setColumnWidth(6, 120); // Time_Spent

      sheet.setRowHeight(1, 35);   // Slightly larger header height
      sheet.setFrozenRows(1);      // Prevents header row scrolling away
    }

    // Extract and process submitted data
    const timestamp = new Date();            // Auto-generated timestamp
    const tasks = data.tasks || [];          // List of tasks user entered
    const totalHours = data.totalHours || 0; // Total hours worked
    
    // Format date for proper storage (YYYY-MM-DD format)
    const formattedDate = data.reportDate || new Date().toISOString().split('T')[0];
    
    // Combine task details into readable multi-line format for the sheet
    // Format: [Category] Description (Xh)
    const tasksCompleted = tasks.map(task => 
      `[${task.category}] ${task.description} (${task.hours}h)`
    ).join("\n");
    
    // Format time spent: "X hrs Y mins" or "X hrs"
    const timeSpent = totalHours % 1 === 0 
      ? `${totalHours} hrs` 
      : `${Math.floor(totalHours)} hrs ${Math.round((totalHours % 1) * 60)} mins`;

    // Final row to insert into sheet - MUST MATCH HEADER ORDER
    const rowData = [
      timestamp,                    // Column 1: Timestamp
      data.email || "",            // Column 2: Email_Address
      data.employeeName || "",     // Column 3: Name
      formattedDate,               // Column 4: Date
      tasksCompleted,              // Column 5: Tasks_Completed
      timeSpent                    // Column 6: Time_Spent
    ];

    // Insert user's work report into the sheet
    sheet.appendRow(rowData);

    const lastRow = sheet.getLastRow(); // Used for styling

    // -----------------
    // FORMATTING BLOCK
    // -----------------
    // These try/catch blocks ensure even if formatting fails,
    // the submission is still saved successfully.

    // Enable wrapping for long descriptions (prevents overflow)
    try {
      const tasksCompletedCell = sheet.getRange(lastRow, 5);
      tasksCompletedCell.setWrap(true);
      tasksCompletedCell.setVerticalAlignment("top");
    } catch (e) {
      Logger.log("Warning: Failed to wrap text → " + e);
    }

    // Apply alternating row colors for cleaner readability
    try {
      if (lastRow % 2 === 0) {
        const rowRange = sheet.getRange(lastRow, 1, 1, 6);
        rowRange.setBackground("#f8f9fa"); // Light gray row pattern
      }
    } catch (e) {
      Logger.log("Warning: Failed alternating row styling → " + e);
    }

    // Format timestamp column
    try {
      const timestampCell = sheet.getRange(lastRow, 1);
      timestampCell.setNumberFormat("yyyy-mm-dd hh:mm:ss");
    } catch (e) {
      Logger.log("Warning: Failed to format timestamp → " + e);
    }

    // Format date column
    try {
      const dateCell = sheet.getRange(lastRow, 4);
      dateCell.setNumberFormat("yyyy-mm-dd");
    } catch (e) {
      Logger.log("Warning: Failed to format date → " + e);
    }

    // Return response confirming success
    return {
      success: true,
      timestamp: timestamp.toISOString(),
      totalTasks: tasks.length,
      totalHours: totalHours,
      sheetName: SHEET_NAME,
      sheetUrl: ss.getUrl()
    };

  } catch (error) {
    // If anything fails, return detailed error message
    Logger.log("ERROR in saveToSheet(): " + error);
    return { success: false, error: error.toString() };
  }
}


/**
 * Utility: Used during development or debugging.
 * Verifies that script can access the spreadsheet and sheet.
 */
function testSheetAccess() {
  try {
    const ss = getSpreadsheet();
    
    Logger.log("Spreadsheet Loaded Successfully:");
    Logger.log("Name: " + ss.getName());
    Logger.log("URL: " + ss.getUrl());

    const sheet = ss.getSheetByName(SHEET_NAME);

    if (sheet) {
      Logger.log(`Sheet '${SHEET_NAME}' exists`);
      Logger.log("Rows stored: " + sheet.getLastRow());
      
      // Verify columns match expected
      const headers = sheet.getRange(1, 1, 1, 6).getValues()[0];
      Logger.log("Current headers: " + JSON.stringify(headers));
      Logger.log("Expected headers: ['Timestamp','Email_Address','Name','Date','Tasks_Completed','Time_Spent']");
    } else {
      Logger.log(`Sheet '${SHEET_NAME}' does NOT exist yet.`);
    }

    return true;

  } catch (error) {
    Logger.log("Sheet Access FAILED → " + error);
    return false;
  }
}


/**
 * Creates the sheet structure manually if needed (useful for first-time setup).
 */
function initializeSheet() {
  try {
    const ss = getSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);

    if (!sheet) {
      // Same formatting as earlier to keep consistency
      sheet = ss.insertSheet(SHEET_NAME);
      sheet.appendRow([
        "Timestamp",
        "Email_Address",
        "Name",
        "Date",
        "Tasks_Completed",
        "Time_Spent"
      ]);

      const headerRange = sheet.getRange(1, 1, 1, 6);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#4285f4");
      headerRange.setFontColor("#ffffff");
      headerRange.setHorizontalAlignment("center");
      headerRange.setBorder(true, true, true, true, true, true);
      
      sheet.setColumnWidth(1, 180);
      sheet.setColumnWidth(2, 200);
      sheet.setColumnWidth(3, 150);
      sheet.setColumnWidth(4, 100);
      sheet.setColumnWidth(5, 500);
      sheet.setColumnWidth(6, 120);
      
      sheet.setFrozenRows(1);

      Logger.log("Sheet created successfully with Python-compatible columns.");
    } else {
      Logger.log("Sheet already exists — no action taken.");
    }

    return true;

  } catch (error) {
    Logger.log("Error initializing sheet → " + error);
    return false;
  }
}


/**
 * Returns statistics about stored submissions.
 * Useful for admin dashboards or reporting.
 */
function getSheetStats() {
  try {
    const ss = getSpreadsheet();
    const sheet = ss.getSheetByName(SHEET_NAME);

    if (!sheet) {
      // No submissions yet
      return {
        totalSubmissions: 0,
        sheetExists: false,
        sheetUrl: ss.getUrl()
      };
    }

    const lastRow = sheet.getLastRow();

    const stats = {
      totalRows: lastRow > 1 ? lastRow - 1 : 0,         // subtract header row
      lastUpdated: lastRow > 1 ? sheet.getRange(lastRow, 1).getValue() : null,
      sheetUrl: ss.getUrl(),
      sheetExists: true
    };

    Logger.log("Sheet Stats: " + JSON.stringify(stats, null, 2));
    return stats;

  } catch (error) {
    Logger.log("Failed to fetch stats → " + error);
    return null;
  }
}
