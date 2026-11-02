// Vault-relative folder you passed to --output. Example: Catechism
const FOLDER = "Catechism";
// Written by scrape_ccc.py next to the index. Maps each number to its link.
const MAP_FILE = "ccc-paragraphs.json";
// Put between links when you ask for more than one paragraph.
const SEPARATOR = " · ";

// "1030", "1030, 1032", and "1030-1032" are all accepted.
function numbersFrom(text) {
	const numbers = [];
	for (const part of String(text).split(/[,;\s]+/)) {
		const range = part.match(/^(\d{1,4})[-–](\d{1,4})$/);
		if (range) {
			const first = Number(range[1]);
			const last = Number(range[2]);
			if (last < first || last - first > 50) return null;
			for (let n = first; n <= last; n++) numbers.push(String(n));
		} else if (/^\d{1,4}$/.test(part)) {
			numbers.push(String(Number(part)));
		} else if (part !== "" && !/^ccc$/i.test(part)) {
			return null;
		}
	}
	return numbers;
}

module.exports = async (params) => {
	const { app, quickAddApi, obsidian } = params;
	const Notice = obsidian.Notice;

	let paragraphs;
	try {
		paragraphs = JSON.parse(await app.vault.adapter.read(`${FOLDER}/${MAP_FILE}`));
	} catch (error) {
		new Notice(`Cannot read ${FOLDER}/${MAP_FILE}. Run scrape_ccc.py --relink first.`);
		return;
	}

	const selected = (quickAddApi.utility.getSelection() || "").trim();
	const term = await quickAddApi.inputPrompt(
		"Link to the Catechism",
		"paragraph number, such as 1030 or 1030-1032",
		selected,
	);
	if (term == null || String(term).trim() === "") return;

	const numbers = numbersFrom(term);
	if (!numbers || numbers.length === 0) {
		new Notice(`Not a paragraph number: ${term}`);
		return;
	}
	const missing = numbers.filter((n) => !paragraphs[n]);
	if (missing.length) {
		new Notice(`No paragraph ${missing.join(", ")} in ${MAP_FILE}.`);
		return;
	}

	const editor = app.workspace.activeEditor && app.workspace.activeEditor.editor;
	if (!editor) {
		new Notice("Open a note in the editor first.");
		return;
	}
	editor.replaceSelection(numbers.map((n) => paragraphs[n].link).join(SEPARATOR));
};
