import fs from 'fs'
import path from 'path'
import postcss from 'postcss'
import cssnano from 'cssnano'
import { fileURLToPath } from 'url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const cssPath = path.resolve(
	scriptDir,
	'../..',
	'erpnext_projekt_hub',
	'public/frontend/assets/frappe-ui.css'
)

if (!fs.existsSync(cssPath)) {
	console.warn(
		`[dedupe-frappe-ui-css] ${cssPath} not found. Run the build first to generate the asset.`
	)
	process.exit(0)
}

const cssContent = fs.readFileSync(cssPath, 'utf8')
const root = postcss.parse(cssContent)

root.walkRules((rule) => {
	const seenProps = new Set()
	rule.walkDecls((decl) => {
		if (seenProps.has(decl.prop)) {
			decl.remove()
		} else {
			seenProps.add(decl.prop)
		}
	})
})

const signatureSet = new Set()
const filteredRoot = postcss.root()

for (const node of root.nodes) {
	const signature = node.toString()
	if (signatureSet.has(signature)) {
		continue
	}
	signatureSet.add(signature)
	filteredRoot.append(node)
}

const minifyCss = async () => {
	const result = await postcss([cssnano({ preset: 'default' })]).process(filteredRoot.toString(), {
		from: cssPath,
		to: cssPath,
	})
	fs.writeFileSync(cssPath, result.css)
	console.log('[dedupe-frappe-ui-css] Cleaned CSS written to', cssPath)
}

minifyCss().catch((error) => {
	console.error('[dedupe-frappe-ui-css] Failed to clean CSS:', error)
	process.exit(1)
})
