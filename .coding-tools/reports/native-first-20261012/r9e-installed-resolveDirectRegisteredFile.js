function resolveDirectRegisteredFile(workspaceRoot, relative) {
  if (typeof workspaceRoot !== 'string' || !path.isAbsolute(workspaceRoot)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED', 'file-read workspace is invalid.');
  }
  const filePath = relativePath(relative, 'CONTROL_PLANE_FILE_READ_PATH_DENIED');
  let root;
  try { root = fs.realpathSync.native(workspaceRoot); }
  catch { throw bridgeError('CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED', 'file-read workspace is unavailable.'); }
  const pathKey = (value) => {
    const normalized = path.normalize(path.resolve(value));
    return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
  };
  if (pathKey(root) !== pathKey(workspaceRoot) || !fs.statSync(root).isDirectory()) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED', 'file-read workspace has changed.');
  }
  const target = path.resolve(root, ...filePath.split('/'));
  if (!pathKey(target).startsWith(`${pathKey(root)}${path.sep}`)) {
    throw bridgeError('CONTROL_PLANE_FILE_READ_PATH_DENIED', 'file path escapes the registered workspace.');
  }
  const parts = filePath.split('/');
  let cursor = root;
  for (const [index, part] of parts.entries()) {
    cursor = path.join(cursor, part);
    let stat;
    let real;
    try {
      stat = fs.lstatSync(cursor);
      real = fs.realpathSync.native(cursor);
    } catch {
      throw bridgeError('CONTROL_PLANE_FILE_READ_TARGET_MISSING', 'file-read target is unavailable.');
    }
    if (stat.isSymbolicLink() || pathKey(real) !== pathKey(cursor)) {
      throw bridgeError('CONTROL_PLANE_FILE_READ_REPARSE_DENIED', 'file-read path contains a reparse point.');
    }
    const final = index === parts.length - 1;
    if (final ? !stat.isFile() : !stat.isDirectory()) {
      throw bridgeError('CONTROL_PLANE_FILE_READ_TARGET_INVALID', 'file-read path is not a direct regular file.');
    }
  }
  return target;
}
