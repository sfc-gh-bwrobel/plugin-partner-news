# Install the partner-news CoCo plugin from GitHub.
# Usage: make install | make uninstall | make reinstall | make status
# Restart CoCo (or reload skills) after install/uninstall to pick up changes.

NAME      := partner-news
OWNER     := sfc-gh-bwrobel
REPO      := plugin-partner-news
REF       ?= main
CLONE_URL ?= git@github.com:$(OWNER)/$(REPO).git
PLUGINS   := $(HOME)/.snowflake/cortex/plugins
DEST      := $(PLUGINS)/$(NAME)
REGISTRY  := $(PLUGINS)/registry.json

.PHONY: install uninstall reinstall status

install:
	@test ! -e "$(DEST)" || { echo "$(DEST) exists - run 'make reinstall'"; exit 1; }
	@mkdir -p "$(PLUGINS)"
	git clone --quiet --depth 1 --branch "$(REF)" "$(CLONE_URL)" "$(DEST)"
	@test -f "$(DEST)/.cortex-plugin/plugin.json" || { echo "No .cortex-plugin/plugin.json in clone"; rm -rf "$(DEST)"; exit 1; }
	@NAME="$(NAME)" OWNER="$(OWNER)" REPO="$(REPO)" REF="$(REF)" REGISTRY="$(REGISTRY)" python3 -c '\
import json, os, datetime; e = os.environ; p = e["REGISTRY"]; o, n, ref = e["OWNER"], e["REPO"], e["REF"]; \
r = json.load(open(p)) if os.path.exists(p) else {}; \
now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"); \
r[e["NAME"]] = {"source": "github:%s/%s#%s" % (o, n, ref), \
 "installedAt": now, "updatedAt": now, "active": True, "lastUpdateError": None, \
 "location": "user", "installKind": "github", \
 "github": {"owner": o, "repo": n, "ref": ref, \
  "cloneUrl": "https://github.com/%s/%s.git" % (o, n)}}; \
json.dump(r, open(p, "w"), indent=2)'
	@echo "Installed $(NAME) from $(OWNER)/$(REPO)@$(REF) into $(DEST)"

uninstall:
	@test -f "$(REGISTRY)" && NAME="$(NAME)" REGISTRY="$(REGISTRY)" python3 -c '\
import json, os; e = os.environ; r = json.load(open(e["REGISTRY"])); \
r.pop(e["NAME"], None); json.dump(r, open(e["REGISTRY"], "w"), indent=2)' || true
	rm -rf "$(DEST)"
	@echo "Uninstalled $(NAME)"

reinstall: uninstall install

status:
	@test -d "$(DEST)" && echo "Installed: $(DEST) ($$(git -C "$(DEST)" rev-parse --short HEAD))" || echo "Not installed"
	@test -f "$(REGISTRY)" && python3 -c 'import json; print(json.dumps(json.load(open("$(REGISTRY)")).get("$(NAME)"), indent=2))' || true
