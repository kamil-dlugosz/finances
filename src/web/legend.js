class HierarchicalLegend {
  constructor(containerId, tierTree, dimensionValues, onChange) {
    this.container = document.getElementById(containerId);
    this.tierTree = tierTree;
    this.dimensionValues = dimensionValues;
    this.onChange = onChange;
    this.checkboxes = {};
    this.render();
  }

  render() {
    this.container.innerHTML = "";
    this.container.style.cssText =
      "font-family:sans-serif;font-size:13px;max-height:80vh;overflow-y:auto;padding:8px;border:1px solid #ddd;border-radius:6px;background:#fafafa;";

    if (Object.keys(this.dimensionValues).length > 0) {
      const dimHeader = document.createElement("strong");
      dimHeader.textContent = "Dimensions";
      dimHeader.style.display = "block";
      dimHeader.style.marginBottom = "4px";
      this.container.appendChild(dimHeader);

      for (const [dimName, values] of Object.entries(this.dimensionValues)) {
        const dimDiv = document.createElement("div");
        dimDiv.style.marginLeft = "8px";
        dimDiv.style.marginBottom = "6px";

        const label = document.createElement("span");
        label.textContent = dimName + ": ";
        label.style.fontWeight = "600";
        dimDiv.appendChild(label);

        for (const val of values) {
          const cb = this._createCheckbox(`dim::${dimName}::${val}`, val, true);
          dimDiv.appendChild(cb.wrapper);
        }
        this.container.appendChild(dimDiv);
      }
    }

    const tierHeader = document.createElement("strong");
    tierHeader.textContent = "Tiers";
    tierHeader.style.cssText = "display:block;margin-top:10px;margin-bottom:4px;";
    this.container.appendChild(tierHeader);

    const tierUl = this._buildTierTree(this.tierTree, 0);
    this.container.appendChild(tierUl);
  }

  _buildTierTree(node, depth) {
    const ul = document.createElement("ul");
    ul.style.cssText = "list-style:none;padding-left:" + (depth > 0 ? 16 : 4) + "px;margin:2px 0;";

    if (typeof node === "object" && !Array.isArray(node)) {
      for (const [key, child] of Object.entries(node)) {
        const li = document.createElement("li");
        const cb = this._createCheckbox(`tier::${depth}::${key}`, key, true);
        li.appendChild(cb.wrapper);

        const childUl = this._buildTierTree(child, depth + 1);
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
        const li = document.createElement("li");
        const cb = this._createCheckbox(`tier::${depth}::${leaf}`, leaf, true);
        li.appendChild(cb.wrapper);
        ul.appendChild(li);
      }
    }
    return ul;
  }

  _createCheckbox(id, labelText, checked) {
    const wrapper = document.createElement("label");
    wrapper.style.cssText = "display:inline-flex;align-items:center;margin-right:8px;cursor:pointer;gap:3px;";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = checked;
    input.id = id;
    input.addEventListener("change", () => this._fireChange());
    wrapper.appendChild(input);
    wrapper.appendChild(document.createTextNode(labelText));
    this.checkboxes[id] = input;
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
    const dims = {};
    const tiers = [];
    for (const [id, cb] of Object.entries(this.checkboxes)) {
      if (id.startsWith("dim::")) {
        const parts = id.split("::");
        const dimName = parts[1];
        const val = parts.slice(2).join("::");
        if (!dims[dimName]) dims[dimName] = [];
        if (cb.checked) dims[dimName].push(val);
      } else if (id.startsWith("tier::") && cb.checked) {
        tiers.push(id.replace(/^tier::\d+::/, ""));
      }
    }
    return { dimensions: dims, tiers };
  }
}
