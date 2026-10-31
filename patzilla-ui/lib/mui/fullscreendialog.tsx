// https://www.typescriptlang.org/docs/handbook/jsx.html
// https://material-ui.com/components/dialogs/#full-screen-dialogs
// https://reactjs.org/docs/state-and-lifecycle.html
// https://charleslbryant.gitbooks.io/hello-react-and-typescript/content/TypeScriptAndReact.html
// https://babeljs.io/blog/2015/07/07/react-on-es6-plus
import React from 'react';
import PropTypes from 'prop-types';
import {SlideProps, Theme} from "@mui/material";
import { withStyles } from '@mui/styles';
import { CSSProperties } from '@mui/styles';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import ListItemText from '@mui/material/ListItemText';
import ListItem from '@mui/material/ListItem';
import List from '@mui/material/List';
import Divider from '@mui/material/Divider';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import Slide from '@mui/material/Slide';
import { TransitionProps } from '@mui/material/transitions';

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
  return <Slide direction="up" ref={ref} {...(props as SlideProps)} />;
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
