const getGlobalWindow = () => (typeof globalThis !== 'undefined' ? globalThis.window : undefined)

export const getRealWindow = () => getGlobalWindow()

export const translate = (text) => {
	const win = getGlobalWindow()
	if (win && typeof win.__ === 'function') {
		return win.__(text)
	}
	return text
}
