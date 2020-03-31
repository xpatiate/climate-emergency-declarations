'use strict';

/*

Create a dropdown of potential parents using data hardcoded into page

When changed, insert a Structure component using data fetched from the structure API
for the structure of the chosen parent

Look at API info on the structure children
if one, show structure and go to next level down
if multiple, show widget for user to choose one


TODO

react:
- force choose between two types of move, only render dropdown after choosing
- reset if they swap between the two
- handle change of descendant structures after first choose

*/

const e = React.createElement;

//https://www.reactenlightenment.com/react-nodes.html

let structureChain = []
let numChildLevels = 0
let areaItems = []
let structureItems = []


// react component which renders the div for moving areas and retaining structures
const MoveAreas = () => {

  // called on change from parent dropdown, after first selection
  const updateParent = (event) => {
    const selectedOpt = event.target.querySelector('option:checked')
    console.log(selectedOpt)
    const hiddenInput = document.querySelector('#single_area_new_parent_id');
    hiddenInput.value = selectedOpt.id
    const structureId = selectedOpt.dataset.structid
    console.log(structureId)
    const structureName = selectedOpt.innerHTML
    console.log(structureName)
    const fillAllDivs = document.querySelectorAll("div[class^='show-dest-structure-']");
    fillAllDivs.forEach(function(el) {
      el.innerHTML = 'unchanged'
    })
    const fillDivs = document.querySelectorAll('.show-dest-parent-1');
    fillDivs.forEach(function(el) {
      el.innerHTML = selectedOpt.innerHTML
    })
  }


  // make dropdown of parent areas + structures for first selection
  const makeParentDropdown = () => {
    console.log("Rendering parent dropdown with a single structure")
    const options = moveParentDataSameStruct.map( function(item) {
      return e('option', {id: item.id, 'data-structid': item.structure_id},
        '(' + item.structure_name + ') ' + item.name
        )
    });
    options.unshift(
      e('option', {id: 0 }, 'Select...')
    )
    const select = e('select', {
      'name': 'new_parent_same_struct',
      'id': 'id_new_parent',
      'onChange': updateParent,
      },
      options);
    areaItems.push(select)
    const hiddenInput = e('input',{
        type: 'hidden',
        id: 'single_area_new_parent_id',
        name: 'area_new_parent_id'
      })
    areaItems.push(hiddenInput)
  }

  if (areaItems.length == 0) {
    makeParentDropdown()
  }
  return e(
    'div', {id: 'select-parent'}, areaItems
  )
}

// react component which renders the div for moving areas AND structures
const MoveStructures = () => {

  // called on change from parent dropdown, after first selection
  const updateParent = (event) => {
    const selectedOpt = event.target.querySelector('option:checked')
    console.log("selectedOpt is " + selectedOpt)
    const hiddenInput = e('input',{
        type: 'hidden',
        name: 'struct_new_parent_id',
        value: selectedOpt.id
      })
    const structureId = selectedOpt.dataset.structid
    console.log(structureId)
    const structureName = selectedOpt.innerHTML
    console.log("structureName is " + structureName)
    structureChain = []
    structureItems = [hiddenInput]
    const childDivs = document.querySelectorAll('.child-from-structure');
    childDivs.forEach(function(c) {
      c.innerHTML = ''
    });
    makeParentDropdown()
    addStructure(structureId)
  }

  // called on change from structure dropdown
  const updateStructure = (event) => {
    const selectedOpt = event.target.querySelector('option:checked')
    console.log(selectedOpt)
    const structureId = selectedOpt.id
    console.log(structureId)
    addStructure(structureId)
    // TODO don't unset the parent dropdown

    // TODO seems to add another level when lowest dropdown is changed
  }

  // when a structure has been chosen, this shows it in the page
  // and looks at its children to determine next step
  const addStructure = (structureId) => {
    const numLevels = window.numChildLevels
    console.log("The areas to move are " + numLevels + " levels high")
    let currentLevel = structureChain.length
    console.log("We currently have " + currentLevel + " structures decided: " + structureChain)

    // Get details on the structure they just chose
    if (structureId) {
      // now fetch structure data from API
      const response = fetch('/api/structures/' + structureId).then(
        function(response) {
          console.log(response)
          const structureData = response.json().then(
            function(structureData) {
              let structLabel = ''
              if (structureChain.length == 0) {
                structLabel = 'New parent structure: ' + structureData['name']
              }
              else {
                structLabel = 'Structure at level ' + structureChain.length + ': ' + structureData['name']
              }
              const showStruct = e('div',
                { class: 'move-structure' },
                structLabel
                )
              const hiddenInput = e('input',{
                  type: 'hidden',
                  name: 'structure_' + structureChain.length,
                  value: structureId
                })
              structureItems.push(showStruct, hiddenInput)
              structureChain.push(structureId)

              const fillDivs = document.querySelectorAll('.show-dest-structure-' + currentLevel);
              fillDivs.forEach(function(el) {
                el.innerHTML = structureData['name']
                el.dataset.id = structureData['id']
                const tableRow = el.parentNode.parentNode;
                const rowChild = tableRow.querySelector('.child-from-structure')
                if (rowChild && (rowChild.dataset.id != el.dataset.id)) {
                  //el.className += ' changing-class'
                  rowChild.innerHTML = '*'
                }
              })


              // Now look at remaining levels and structures
              currentLevel = structureChain.length
              let structureOpts = []
              const remainingLevels = numLevels - currentLevel
              console.log("total levels " + numLevels + " - current level " + currentLevel)
              console.log(' there are ' + remainingLevels + ' remaining levels')
              if (remainingLevels >= 0) {
                console.log('structure at ' + currentLevel + ' is ' + structureChain[currentLevel])
                structureData['children'].forEach( function(child) {
                  console.log('child ' + child['name'] + ' has ' + child['height'] + ' children')
                  if (child['height']  >= remainingLevels) {
                    structureOpts.push(child)
                  }
                  else {
                    console.log("Can't add " + child['name'] + ", height " + child['height'] + " < remaining levels " + remainingLevels)
                  }
                });
                console.log(structureOpts)
                if (structureOpts.length == 1) {
                  // we only have one potential structure for the next level down
                  // so just assume we are using it
                  addStructure(structureOpts[0]['id'])
                }
                else if (structureOpts.length == 0) {
                  console.log("oops, no remaining structures")
                }
                else {
                  // make a structure dropdown and insert it
                  console.log("inserting a structure dropdown")
                  makeStructureDropdown(structureOpts, structureChain.length)
                }
              }
              console.log("now re-rendering component")
              const reContainer = document.querySelector('#move_structure_controls');
              ReactDOM.render(e(MoveStructures), reContainer);
            });
        });

    }
    console.log("structureItems:")
    console.log(structureItems)

    // what if areas are moving to a parent of the same structure?
    // then don't need to define child structures

  }

  // make dropdown of structures for descendant levels
  const makeStructureDropdown = (structureOpts, level) => {
    const options = structureOpts.map( function(item) {
      return e('option', {id: item.id, 'data-structid': item.structure_id}, 
        item.name
        )
    });
    options.unshift(
      e('option', {id: 0 }, 'Select...')
    )
    const select = e('select', {
      'name': 'structure_' + level,
      'id': 'structure_' + level,
      'onChange': updateStructure,
      },
      options);
    structureItems.push(select)
  }

  // make dropdown of parent areas + structures for first selection
  const makeParentDropdown = () => {
    console.log("Rendering parent dropdown of all possible structures")
    console.log(moveParentDataAllStructs)
    const options = moveParentDataAllStructs.map( function(item) {
      return e('option', {id: item.id, 'data-structid': item.structure_id}, 
        '(' + item.structure_name + ') ' + item.name
        )
    });
    options.unshift(
      e('option', {id: 0 }, 'Select...')
    )
    const select = e('select', {
      'name': 'new_parent',
      'id': 'id_new_parent',
      'onChange': updateParent,
      },
      options);
    structureItems.push(select)
  }

  if (structureItems.length == 0) {
    makeParentDropdown()
  }
  return e(
    'div', {id: 'select-structure'}, structureItems
  )
}
