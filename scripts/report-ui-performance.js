const fs = require('node:fs');
const path = require('node:path');

function fail(code, message) {
  process.stderr.write(`UI_PERFORMANCE_REPORT ERROR code=${code} message=${message}\n`);
  process.exitCode = 1;
}

const appData = String(process.env.APPDATA || '').trim();
const reportPath = String(process.argv.find((argument) => argument.startsWith('--path=')) || '').slice('--path='.length).trim()
  || (appData ? path.join(appData, 'web-mcp-assistant', 'ui-performance.json') : '');

if (!reportPath) {
  fail('APPDATA_UNAVAILABLE', 'The installed Electron profile path could not be resolved.');
} else if (!fs.existsSync(reportPath)) {
  fail('MEASUREMENT_NOT_FOUND', `No bounded Electron UI measurement exists at ${reportPath}.`);
} else {
  try {
    const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    if (report?.schema_version !== 1 || report?.kind !== 'electron_ui_real_machine_performance_window') {
      throw Object.assign(new Error('Unsupported UI performance report schema.'), { code: 'SCHEMA_INVALID' });
    }
    if (!report.summary || typeof report.summary !== 'object' || Array.isArray(report.summary)) {
      throw Object.assign(new Error('UI performance report summary is missing.'), { code: 'SUMMARY_MISSING' });
    }
    process.stdout.write(`${JSON.stringify({
      source_path: reportPath,
      schema_version: report.schema_version,
      kind: report.kind,
      context: report.context || {},
      window: report.window || {},
      limits: report.limits || {},
      summary: report.summary
    }, null, 2)}\n`);
  } catch (error) {
    fail(error?.code || 'REPORT_INVALID', error?.message || 'The UI performance report is invalid.');
  }
}
