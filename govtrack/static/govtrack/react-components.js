'use strict';

/*

Create a dropdown of potential parents using data hardcoded into page

When changed, insert a Structure component using data fetched from the structure API
for the structure of the chosen parent

Look at API info on the structure children
if one, show structure and go to next level down
if multiple, show widget for user to choose one



So need components:
- parent chooser
- structure display
- structure choose

*/

const e = React.createElement;

class LikeButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = { liked: false };
  }

  render() {
    if (this.state.liked) {
      return 'You liked this.';
    }

    return e(
      'button',
      { onClick: () => this.setState({ liked: true }) },
      'Like'
    );
  }
}

//https://www.reactenlightenment.com/react-nodes.html

let structureChain = []
let numChildLevels = 0
let itemsToRender = []


// react component which renders the whole dynamic div
const MoveAreas = () => {

  // called on change from parent dropdown, after first selection
  const setParent = (event) => {
    const selectedOpt = event.target.querySelector('option:checked')
    console.log(selectedOpt)
    const structureId = selectedOpt.dataset.structid
    console.log(structureId)
    const structureName = selectedOpt.innerHTML
    console.log(structureName)
    structureChain = []
    itemsToRender = []
    makeParentDropdown()
    setupStructure(structureId)
  }

  // when a structure has been chosen, this shows it in the page
  // and looks at its children to determine next step
  const setupStructure = (structureId) => {
    const numLevels = window.numChildLevels
    console.log("The areas to move are " + numLevels + " levels high")
    let numStructures = structureChain.length
    console.log("We currently have " + numStructures + " structures decided")

    // Get details on the structure they just chose
    if (structureId) {
      // now fetch structure data from API
      const response = fetch('/api/structures/' + structureId).then(
        function(response) {
          console.log(response)
          const structureData = response.json().then(
            function(structureData) {
              const showStruct = e('div',
                { class: 'move-structure' },
                'Level ' + structureChain.length + ': ' + structureData['name']
                )
              const hiddenInput = e('input',{
                  type: 'hidden',
                  name: 'structure_' + structureChain.length,
                  value: structureId
                })
              itemsToRender.push(showStruct, hiddenInput)
              structureChain.push(structureId)


              // Now look at remaining levels and structures
              let structureOpts = []
              const remainingLevels = numLevels - numStructures
              console.log(' there are ' + remainingLevels + ' remaining levels')
              if (remainingLevels > 0) {
                structureData['children'].forEach( function(child) {
                  console.log('child ' + child['name'] + ' has ' + child['height'] + ' children')
                  if (child['height']  >= remainingLevels) {
                    structureOpts.push(child)
                  }
                });
                if (structureOpts.length == 1) {
                  // we only have one potential structure for the next level down
                  // so just assume we are using it
                  setupStructure(structureOpts[0]['id'])
                }
                else {
                  // make a structure dropdown and insert it
                  console.log("inserting a structure dropdown")
                }
              }
              console.log("now re-rendering component")
              const reContainer = document.querySelector('#move_areas');
              ReactDOM.render(e(MoveAreas), reContainer);
            });
        });

    }
    console.log("itemsToRender:")
    console.log(itemsToRender)

    // for each level in numChildLevels:

    // structure has one kid? show unchangeable kid structure
    // structure has multiple kids? show a choice of available structures

    // when chosen, go to next level


    // re-render element

  }

  // make dropdown of parent areas + structures for first selection
  const makeParentDropdown = () => {
    console.log("Rendering move areas stuff")
    const options = moveParentData.map( function(item) {
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
      'onChange': setParent,
      },
      options);
    itemsToRender.push(select)
  }

  if (itemsToRender.length == 0) {
    makeParentDropdown()
  }
  return e(
    'div', {id: 'my-structure'}, itemsToRender
  )
}
