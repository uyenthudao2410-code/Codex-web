const { createRuntimeDependencies, refreshLifecycle } = require('../scripts/dev-ui-lifecycle');

(async () => {
  const deps = createRuntimeDependencies({
    timeoutMs: 2000,
    pollMs: 100,
    output: (line) => console.log(`OUT ${line}`)
  });
  try {
    const result = await refreshLifecycle(deps);
    console.log('RESULT', JSON.stringify(result));
  } catch (error) {
    console.log('ERROR', error.code, error.message, JSON.stringify(error.details || {}));
    console.log(error.stack);
  }
})();
