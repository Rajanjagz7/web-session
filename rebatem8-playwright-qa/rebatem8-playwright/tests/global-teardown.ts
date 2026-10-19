import {rm} from 'node:fs/promises';
export default async function teardown() { await rm('.auth', {recursive: true, force: true}); }
