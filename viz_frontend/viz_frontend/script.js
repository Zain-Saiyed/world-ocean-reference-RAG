d3.json('hierarchical_output.json').then(data => {
  var clusterName;
  const width = 850;
  const height = 1000;

  const color = d3.scaleLinear()
      .domain([0, 5])
      .range(["hsl(195, 100%, 75%)", "hsl(210, 100%, 40%)"])
      .interpolate(d3.interpolateHcl);

  const pack = data => d3.pack()
      .size([width, height])
      .padding(3)
    (d3.hierarchy(data)
      .sum(d => d.value)
      .sort((a, b) => b.value - a.value));
  const root = pack(data);

  const backgroundColor = d3.color(color(0)).rgb();
  const backgroundColorWithTransparency = `rgba(${backgroundColor.r}, ${backgroundColor.g}, ${backgroundColor.b}, 0.1)`; // Adjust the 0.5 for desired transparency

const svg = d3.create("svg")
  .attr("viewBox", `-${width / 2} -${height / 2} ${width} ${height}`)
  .attr("width", width)
  .attr("height", height)
  .attr("style", `max-width: 100%; height: auto; display: block; margin: 0 -10px; background: ${backgroundColorWithTransparency}; cursor: pointer;`);

  const nodeMap = new Map();

  const clusterMapping = generateClusterMapping(root.descendants());

  const node = svg.append("g")
    .selectAll("circle")
    .data(root.descendants().slice(1))
    .join("circle")
      .attr("fill", d => d.children ? color(d.depth) : "white")
      .attr("pointer-events", d => !d.children ? "none" : null)
      .attr("data-id", d => d.data.name) // Store data-id for easier access
      .attr("transform", d => `translate(${d.x},${d.y})`)
      .on("mouseover", function(event, d) { 
        d3.select(this).attr("stroke", "#000");
        highlightNode(d, true);
        createOrUpdateNumberDisplay(d3.select("body"), "Cluster name", d.data.name);
    })
      .on("mouseout", function(event, d) { 
          d3.select(this).attr("stroke", null);
          highlightNode(d, false);
          //removeNumberDisplay("Cluster name");
      })
      .on("click", (event, d) => focus !== d && (zoom(event, d), event.stopPropagation()));

  node.each(function(d) {
    nodeMap.set(d.data.name, d3.select(this));
  });

  const label = svg.append("g")
      .style("font", "18px sans-serif")
      .attr("pointer-events", "none")
      .attr("text-anchor", "middle")
    .selectAll("text")
    .data(root.descendants())
    .join("text")
      .style("fill-opacity", d => d.parent === root ? 1 : 0)
      .style("display", d => d.parent === root ? "inline" : "none");

  svg.on("click", (event) => zoom(event, root));
  let focus = root;
  let view;
  zoomTo([focus.x, focus.y, focus.r * 2]);

  function zoomTo(v) {
    const k = width / v[2];

    view = v;

    label.attr("transform", d => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`);
    node.attr("transform", d => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`);
    node.attr("r", d => d.r * k);
  }

  let displayBoxVisible = false; 

  function zoom(event, d) {
    const focus0 = focus;

    focus = d;
    clusterName = clusterMapping[d.data.name];

    if (!displayBoxVisible) {
      createOrUpdateNumberDisplay(d3.select("body"), "Cluster name", d.data.name);
      displayBoxVisible = true;
    }

    const transition = svg.transition()
        .duration(event.altKey ? 7500 : 750)
        .tween("zoom", d => {
          const i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2]);
          return t => zoomTo(i(t));
        });

    label
      .filter(function(d) { return d.parent === focus || this.style.display === "inline"; })
      .transition(transition)
        .style("fill-opacity", d => d.parent === focus ? 1 : 0)
        .on("start", function(d) { if (d.parent === focus) this.style.display = "inline"; })
        .on("end", function(d) { if (d.parent !== focus) this.style.display = "none"; });

        // Hide the display box when zooming out
  if (focus === root && displayBoxVisible) {
    removeNumberDisplay("Cluster name");
    displayBoxVisible = false;
  }
  }

  document.body.appendChild(svg.node());

  // Function to create or update number display
  function createOrUpdateNumberDisplay(container, label, value) {
    let display = d3.select(`#display-${label.replace(/\s+/g, '-')}`);

  if (display.empty()) {
    display = d3.select('body').append('div')
      .attr('id', `display-${label.replace(/\s+/g, '-')}`)
      .attr('class', 'attribute-display');
    display.append('div').attr('class', 'label').text(label);
    display.append('div').attr('class', 'value');
  }

  display.select('.value').text(value);
  }

  // Function to remove the number display
  function removeNumberDisplay(label) {
    d3.select(`#display-${label.replace(/\s+/g, '-')}`).remove();
  }

  // Function to highlight only the hovered node and its children
  function highlightNode(d, highlight) {
      // Highlight the hovered node
      const hoveredNode = nodeMap.get(d.data.name);
      if (hoveredNode) {
        hoveredNode.attr("stroke", highlight ? "#f00" : null)
                   .attr("stroke-width", highlight ? "2px" : null);
      }
      
      // Highlight the children nodes in green
      if (d.children) {
        d.children.forEach(child => {
          const childNode = nodeMap.get(child.data.name);
          if (childNode) {
            childNode.attr("stroke", highlight ? "green" : null)
                     .attr("stroke-width", highlight ? "2px" : null);
          }
        });
      }
  }
  
  // Function to generate cluster identifier mapping
  function generateClusterMapping(nodes) {
    const mapping = {};
    let count = 1;
    nodes.forEach(node => {
      if (node.depth === 1) { // Adjust the depth condition based on your hierarchy
        mapping[node.data.name] = `CLS_${count}`;
        count++;
      }
    });
    return mapping;
  }

  document.getElementById('go-button').addEventListener('click', () => {
    const userQuery = document.getElementById('user-query').value;
    const mode = document.getElementById('mode').value;
    const modelName = document.getElementById('model').value;
    
    // Show loading icon
    document.getElementById('loading-icon').style.display = 'block';

    // Prepare the data
    const postData = {
      cluster_name: clusterName,
      user_query: userQuery,
      mode: mode,
      modelName: modelName
    };

    // CORS proxy URL
    const corsProxy = 'http://localhost:8080/';
   const apiUrl = 'http://134.190.153.189:8401/api';
    // const apiUrl = 'http://localhost:8401/api';

    // Make the POST request
    fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(postData)
    })
    .then(response => response.json())
    .then(data => {
      console.log('Success:', data);
      if (data.llm_response) {
        if (data.llm_response.llama3) {
          alert(data.llm_response.llama3);
        } else if (data.llm_response.phi3) {
          alert(data.llm_response.phi3);
        } else {
          alert("No valid llm_response found");
        }
      } else {
        alert("No llm_response found");
      }
    })
    .catch((error) => {
      console.error('Error:', error);
    })
    .finally(() => {
      // Hide loading icon
      document.getElementById('loading-icon').style.display = 'none';
    });
  });
});
