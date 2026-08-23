(() => {
  const api = window.mcpAssistant;
  const local = { prepared: false };
  const $ = (selector) => document.querySelector(selector);

  function unwrap(result) {
    if (!result?.ok) {
      const error = result?.error;
      throw new Error(error?.message || (typeof error === 'string' ? error : 'P5-A0 control failed'));
    }
    return result.data;
  }

  function epochFrom(payload) {
    const value = payload?.p5;
    return value?.epoch?.epoch || value?.epoch || (value?.activation_epoch_id ? value : null);
  }

  function render(payload, action = 'status') {
    const epoch = epochFrom(payload);
    const lifecycle = String(epoch?.lifecycle || payload?.p5?.lifecycle || 'NOT_OPEN');
    const source = payload?.source_contract || payload?.verified_contract?.source || {};
    const environment = payload?.environment_contract || payload?.verified_contract?.environment || {};
    const seed = payload?.p5_seed || {};
    if (payload?.p5?.prepared === true) local.prepared = true;
    if (action === 'open') local.prepared = false;
    $('#p5A0Status').textContent = lifecycle;
    const sourceClean = source.source_worktree_clean === true ? 'clean' : source.source_worktree_clean === false ? 'dirty' : 'unknown';
    const upstream = source.head_matches_upstream === true ? 'upstream matched' : source.head_matches_upstream === false ? 'upstream drift' : 'upstream unknown';
    $('#p5A0Source').textContent = sourceClean + ' · ' + upstream;
    $('#p5A0Environment').textContent = String(environment.environment_fp || '—').slice(0, 16);
    $('#p5A0Seed').textContent = seed.available === true ? String(seed.seed_commitment_sha256 || 'ready').slice(0, 16) : 'unavailable';
    const identity = payload?.p5?.manifest_sha256 || payload?.p5?.activation_epoch_id || epoch?.activation_epoch_id || '';
    $('#p5A0Manifest').textContent = String(identity || '—').slice(0, 16);
    const funnel = payload?.p5?.funnel;
    const integrity = payload?.p5?.integrity;
    $('#p5A0Detail').textContent = funnel ? 'A0 ' + lifecycle + ' · assigned ' + (funnel.assigned ?? 0) + ' · terminal ' + (funnel.terminal_finalized ?? 0) + ' · hard-stop ' + (integrity?.hard_stop_required === true ? 'required' : 'no') : 'A0 ' + lifecycle + ' · seed ' + (seed.available === true ? 'ready' : 'unavailable') + ' · prepare ' + (local.prepared ? 'ready' : 'required');
    $('#p5A0Open').disabled = !local.prepared;
    $('#p5A0Pause').disabled = lifecycle !== 'EPOCH_ACTIVE';
    $('#p5A0Resume').disabled = lifecycle !== 'EPOCH_PAUSED';
    $('#p5A0Close').disabled = !['EPOCH_ACTIVE', 'EPOCH_PAUSED'].includes(lifecycle);
    $('#p5A0HardStop').disabled = !['EPOCH_ACTIVE', 'EPOCH_PAUSED'].includes(lifecycle);
    $('#p5A0Analyze').disabled = lifecycle === 'NOT_OPEN';
  }

  async function invoke(action) {
    try {
      if (!api?.p5A0) throw new Error('P5-A0 IPC is unavailable in this runtime.');
      const payload = unwrap(await api.p5A0(action));
      render(payload, action);
      if (!['status', 'prepare', 'analyze'].includes(action)) render(unwrap(await api.p5A0('status')), 'status');
    } catch (error) {
      local.prepared = false;
      $('#p5A0Status').textContent = 'Unavailable';
      $('#p5A0Detail').textContent = error?.message || String(error);
    }
  }

  function bind() {
    if (!$('#p5A0Card')) return;
    $('#p5A0Refresh').addEventListener('click', () => invoke('status'));
    $('#p5A0Prepare').addEventListener('click', () => invoke('prepare'));
    $('#p5A0Open').addEventListener('click', () => invoke('open'));
    $('#p5A0Analyze').addEventListener('click', () => invoke('analyze'));
    $('#p5A0Pause').addEventListener('click', () => invoke('pause'));
    $('#p5A0Resume').addEventListener('click', () => invoke('resume'));
    $('#p5A0Close').addEventListener('click', () => { if (window.confirm('Đóng P5-A0 epoch hiện tại?')) invoke('close'); });
    $('#p5A0HardStop').addEventListener('click', () => { if (window.confirm('Hard-stop P5-A0 epoch hiện tại? Chỉ dùng khi integrity/authority có vấn đề.')) invoke('hard_stop'); });
    invoke('status');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind, { once: true });
  else bind();
})();
