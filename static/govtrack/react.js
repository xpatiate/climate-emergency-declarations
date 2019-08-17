'use strict';

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

function Deleter(props) {
    return e(
      'a',
      { onClick: function(){
        const response = confirm('are you sure?');
        console.log(response);
        if (response) {
            const areaid = '#' + props.id;
            const maindiv = document.querySelector(areaid);
            maindiv.style.display='none';
            console.log('making API call for ' + areaid + ' to ' + props.url);
            //TODO make this a POST with CSRF
            var oReq = new XMLHttpRequest();
            oReq.open("GET", props.url);
            oReq.send();
        }
      }},
      'X'
    );
}

const allContainers = document.querySelectorAll('.react-delete-link');
for (var f = 0, len = allContainers.length; f < len; f++) {
    const c = allContainers[f];
    ReactDOM.render(e(Deleter,{url: c.dataset.url, id: c.id}), c);
}
