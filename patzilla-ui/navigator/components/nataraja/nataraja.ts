import { DialogWidget } from 'patzilla.lib.mui.dialog';

const log = console.log;

export default class Nataraja {
    /**
     * Changes.
     */

    foobar: any;
    left: any;
    right: any;

    constructor(message: string) {
        this.foobar = message;
    }

    select_left(element) {
        this.left = element;
    }

    select_right(element) {
        this.right = element;
        this.open_diff();
    }

    open_diff() {
        log('left:', this.left);
        log('right:', this.right);
        var dialog = new DialogWidget();
        dialog.show('abc', {});
    }
}
