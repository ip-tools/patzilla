// https://www.typescriptlang.org/docs/handbook/jsx.html
// https://material-ui.com/components/dialogs/#full-screen-dialogs
// https://reactjs.org/docs/state-and-lifecycle.html
// https://charleslbryant.gitbooks.io/hello-react-and-typescript/content/TypeScriptAndReact.html
// https://babeljs.io/blog/2015/07/07/react-on-es6-plus
import React from 'react';
import PropTypes from 'prop-types';
import { Theme, withStyles } from '@material-ui/core/styles';
import { CSSProperties } from '@material-ui/styles';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import ListItemText from '@material-ui/core/ListItemText';
import ListItem from '@material-ui/core/ListItem';
import List from '@material-ui/core/List';
import Divider from '@material-ui/core/Divider';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import CloseIcon from '@material-ui/icons/Close';
import Slide from '@material-ui/core/Slide';
import { TransitionProps } from '@material-ui/core/transitions';

const log = console.log;


// Define CSS style.
const styles: (theme: Theme) => Record<string, CSSProperties> = (theme) => ({
  appBar: {
    position: 'relative',
  },
  title: {
    marginLeft: theme.spacing(2),
    flex: 1,
  },
});

// Define animation.
const Transition = React.forwardRef<unknown, TransitionProps>(function Transition(props, ref) {
  return <Slide direction="up" ref={ref} {...props} />;
});


// Component properties.
interface FullScreenDialogProps {
  open?: boolean;
  classes?: any;
}

// Component state.
interface FullScreenDialogState {
  open?: boolean;
}

// Component.
class FullScreenDialog extends React.Component<FullScreenDialogProps, FullScreenDialogState> {

  constructor(props) {
    super(props);
    this.state = {open: this.props.open};
  }

  /*
  open() {
    this.setState({isOpen: true});
  }
  */

  /*
  handleClickOpen() {
    this.setState({isOpen: true});
  }
  */

  handleClose = () => {
    this.setState({open: false});
  }

  render() {

    // Acquire "open" from state object, default value using object destructuring.
    // https://basarat.gitbooks.io/typescript/content/docs/destructuring.html
    const { open = false } = this.state;

    // Acquire "classes" from props object.
    const classes = this.props.classes;

    return (
      <div>
        <Dialog fullScreen open={open} onClose={this.handleClose} TransitionComponent={Transition}>
          <AppBar className={classes.appBar}>
            <Toolbar>
              <IconButton edge="start" color="inherit" onClick={this.handleClose} aria-label="Close">
                <CloseIcon />
              </IconButton>
              <Typography variant="h6" className={classes.title}>
                ACME
              </Typography>
              <Button color="inherit" onClick={this.handleClose}>
                save
              </Button>
            </Toolbar>
          </AppBar>
          <List>
            <ListItem button>
              <ListItemText primary="FooBar" secondary="Titania" />
            </ListItem>
            <Divider />
            <ListItem button>
              <ListItemText primary="BazQux" secondary="Tethys" />
            </ListItem>
          </List>
        </Dialog>
      </div>
    );
  }
}

export default withStyles(styles, {withTheme: true})(FullScreenDialog);
