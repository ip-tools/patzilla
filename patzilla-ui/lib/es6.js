export { classes };

/**
 *
 * Support for mixin-style inheritance by extending from expressions yielding function objects.
 * [Notice: the generic aggregation function is usually provided by a library like this one, of course]
 *
 * http://es6-features.org/#ClassInheritanceFromExpressions
 *
 */

var aggregation = (baseClass, ...mixins) => {
    let base = class _Combined extends baseClass {
        constructor(...args) {
            super(...args);
            mixins.forEach((mixin) => {
                mixin.prototype.initializer.call(this);
            });
        }
    };
    let copyProps = (target, source) => {
        Object.getOwnPropertyNames(source).concat(Object.getOwnPropertySymbols(source)).forEach((prop) => {
            if (prop.match(/^(?:constructor|prototype|arguments|caller|name|bind|call|apply|toString|length)$/)) return Object.defineProperty(target, prop, Object.getOwnPropertyDescriptor(source, prop))
        })
    }
    mixins.forEach((mixin) => {
        copyProps(base.prototype, mixin.prototype);
        copyProps(base, mixin);
    });
    return base;
};


/**
 *
 * Multiple Inheritance in JS — Part 2
 *
 * https://itnext.io/multiple-inheritance-in-js-part-2-24adca2c2518
 * https://gist.github.com/zhirzh/fbfe28ca0f33f14f22a025c914f1d0e3
 *
 */

function inheritsObject(baseObject, superObject) {
  Object.setPrototypeOf(baseObject, superObject);
}

function inheritsMultipleObjects(baseObject, superObjects) {
  inheritsObject(
    baseObject,

    new Proxy({}, {
      get(target, key, rec) {
        const parent = superObjects.find(p => Reflect.has(p, key));

        if (parent !== undefined) {
          return Reflect.get(parent, key);
        }

        return undefined;
      },

      has(target, key) {
        const parentHasKey = superObjects.some(p => Reflect.has(p, key));

        if (parentHasKey) {
          return true;
        }

        return false;
      }
    })
  );
}

function inheritsMultipleConstructors(BaseCtor, SuperCtors) {
  return new Proxy(BaseCtor, {
    construct(_, [baseArgs = [], superArgs = []], newTarget) {
      let instance = {};

      instance = SuperCtors.reduce((acc, Ctor, i) => {
        const args = superArgs[i] || [];
        return Object.assign(acc, new Ctor(...args));
      }, instance);

      instance = Object.assign(instance, new BaseCtor(...baseArgs));

      inheritsObject(instance, BaseCtor.prototype);
      return instance;
    }
  });
}

function inheritsMultiple(BaseCtor, SuperCtors) {
  inheritsMultipleObjects(
    BaseCtor.prototype,
    SuperCtors.map(Ctor => Ctor.prototype)
  );

  return inheritsMultipleConstructors(BaseCtor, SuperCtors);
}


/**
 * Simple aggregator for doing ES6-style property
 * overwriting based on `Object.assign()`.
 *
 * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/assign
 * http://2ality.com/2014/01/object-assign.html
 *
 */
const classes = {

    many: function(baseclass, ...mixins) {
        class remixed extends baseclass {}
        Object.assign(remixed.prototype, ...mixins);
        return remixed;
    }
};


/*
 * ==============
 * More resources
 * ==============
 *
 * https://javascript.info/mixins
 * http://raganwald.com/2015/06/17/functional-mixins.html
 * http://raganwald.com/2015/06/26/decorators-in-es7.html
 *
 *
 * =====================
 * Other implementations
 * =====================
 *
 * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes#Mix-ins
 *
 * http://cocktailjs.github.io/
 * https://github.com/CocktailJS/cocktail
 *
 * https://www.npmjs.com/package/backbone.cocktail
 * https://github.com/onsi/cocktail
 *
 * http://justinfagnani.com/2015/12/21/real-mixins-with-javascript-classes/
 * https://github.com/justinfagnani/mixwith.js
 *
 * https://traitsjs.github.io/traits.js-website/
 *
 */
