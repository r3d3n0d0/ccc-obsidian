// Vault-relative folder you passed to --output. Example: Catechism
const FOLDER = "Catechism";

module.exports = async (params) => {
	const { app, quickAddApi, obsidian } = params;
	const selected = (quickAddApi.utility.getSelection() || "").trim();
	const term = await quickAddApi.inputPrompt(
		"Search the Catechism",
		"words or a phrase",
		selected,
	);
	if (term == null || String(term).trim() === "") return;

	const cleaned = String(term).trim().replace(/"/g, "");
	const useOr = /\bOR\b/.test(cleaned);
	// Square brackets start a property search in Obsidian, so they cannot stay in the query.
	const phrase = cleaned.replace(/[()[\]]/g, " ").replace(/\s+/g, " ").trim();
	const body = useOr ? phrase : `"${phrase}"`;
	if (body === '""' || body === "") return;

	const query = `path:"${FOLDER}" ${body}`;
	const searchPlugin = app.internalPlugins.getPluginById("global-search");
	const search = searchPlugin && searchPlugin.instance;
	if (!search || typeof search.openGlobalSearch !== "function") {
		const Notice = obsidian.Notice;
		new Notice("Obsidian search is turned off.");
		return;
	}
	search.openGlobalSearch(query);
};
