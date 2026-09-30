// Execute the unchanged MIT upstream module, rather than a reconstructed oracle.
import { isPrintModeHeadlessOneShotCommand } from './print-mode-headless-command.ts'
import fs from 'node:fs'
const cases = JSON.parse(fs.readFileSync(0, 'utf8'))
process.stdout.write(JSON.stringify(cases.map(isPrintModeHeadlessOneShotCommand)))
