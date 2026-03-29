class HierarchicalLegend {
  constructor(containerId, tierTree, onChange) {
    this.container = document.getElementById(containerId);
    this.tierTree = tierTree;
    this.onChange = onChange;
    this.checkboxes = {};
    this.render();
  }

  render() {
    this.container.innerHTML = "";
    this.container.style.cssText =
      "font-family:sans-serif;font-size:13px;max-height:80vh;overflow-y:auto;padding:8px;border:1px solid #ddd;border-radius:6px;background:#fafafa;";

    const tierHeader = document.createElement("strong");
    tierHeader.textContent = "Tiers";
    tierHeader.style.cssText = "display:block;margin-bottom:4px;";
    this.container.appendChild(tierHeader);

    const tierUl = this._buildTierTree(this.tierTree, 0, "");
    this.container.appendChild(tierUl);
  }

  _buildTierTree(node, depth, pathPrefix) {
    const ul = document.createElement("ul");
    ul.style.cssText = "list-style:none;padding-left:" + (depth > 0 ? 16 : 4) + "px;margin:2px 0;";
    const prefix = pathPrefix || "";

    if (typeof node === "object" && !Array.isArray(node)) {
      for (const [key, child] of Object.entries(node)) {
        const fullPath = prefix ? prefix + "/" + key : key;
        const li = document.createElement("li");
        const cb = this._createCheckbox(`tier::${fullPath}`, key, true);
        li.appendChild(cb.wrapper);

        const childUl = this._buildTierTree(child, depth + 1, fullPath);
        li.appendChild(childUl);

        cb.input.addEventListener("change", () => {
          const childCbs = childUl.querySelectorAll('input[type="checkbox"]');
          childCbs.forEach((c) => (c.checked = cb.input.checked));
          this._fireChange();
        });

        const childInputs = childUl.querySelectorAll('input[type="checkbox"]');
        childInputs.forEach((ci) => {
          ci.addEventListener("change", () => {
            this._updateParentState(cb.input, childUl);
            this._fireChange();
          });
        });

        ul.appendChild(li);
      }
    } else if (Array.isArray(node)) {
      for (const leaf of node) {
        const fullPath = prefix ? prefix + "/" + leaf : leaf;
        const li = document.createElement("li");
        const cb = this._createCheckbox(`tier::${fullPath}`, leaf, true);
        li.appendChild(cb.wrapper);
        ul.appendChild(li);
      }
    }
    return ul;
  }

  _createCheckbox(mapKey, labelText, checked) {
    const wrapper = document.createElement("label");
    wrapper.style.cssText = "display:inline-flex;align-items:center;margin-right:8px;cursor:pointer;gap:3px;";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = checked;
    input.addEventListener("change", () => this._fireChange());
    wrapper.appendChild(input);
    wrapper.appendChild(document.createTextNode(labelText));
    this.checkboxes[mapKey] = input;
    return { wrapper, input };
  }

  _updateParentState(parentCb, childUl) {
    const children = childUl.querySelectorAll(":scope > li > label > input");
    const checked = Array.from(children).filter((c) => c.checked).length;
    if (checked === 0) {
      parentCb.checked = false;
      parentCb.indeterminate = false;
    } else if (checked === children.length) {
      parentCb.checked = true;
      parentCb.indeterminate = false;
    } else {
      parentCb.checked = false;
      parentCb.indeterminate = true;
    }
  }

  _fireChange() {
    const state = this.getState();
    if (this.onChange) this.onChange(state);
  }

  getState() {
    const tierSet = new Set();
    for (const [key, cb] of Object.entries(this.checkboxes)) {
      if (key.startsWith("tier::") && cb.checked) {
        for (const seg of key.slice(6).split("/")) tierSet.add(seg);
      }
    }
    return { tiers: Array.from(tierSet) };
  }
}
