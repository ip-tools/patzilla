-- -*- coding: utf-8 -*-
-- (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>


-- ------------------------------------------
--  http utilities
-- ------------------------------------------

function get_uri(path, args, args_more)
    local uri_args = deepcopy(args)
    table_merge(uri_args, args_more)
    return path .. '?' .. ngx.encode_args(uri_args)
end

function decode_uri(uri)

    if uri == nil then
        return '', {}
    end

    local path, args = uri:match('(.+)?(.+)')
    if not path then
        path = uri
    end
    if args then
        args = ngx.decode_args(args)
    else
        args = {}
    end
    --ngx.log(ngx.ERR, 'args: ' .. args.came_from)
    return path, args
end

function decode_referer()
    return decode_uri(ngx.var.http_referer)
end


-- ------------------------------------------
--  generic utilities
-- ------------------------------------------

function table_merge(target, new)
    for k,v in pairs(new) do target[k] = v end
end

-- http://stackoverflow.com/questions/2282444/how-to-check-if-a-table-contains-an-element-in-lua
function table_contains(table, element)
  for _, value in pairs(table) do
    if value == element then
      return true
    end
  end
  return false
end

-- http://lua-users.org/wiki/CopyTable
function deepcopy(orig)
    local orig_type = type(orig)
    local copy
    if orig_type == 'table' then
        copy = {}
        for orig_key, orig_value in next, orig, nil do
            copy[deepcopy(orig_key)] = deepcopy(orig_value)
        end
        setmetatable(copy, deepcopy(getmetatable(orig)))
    else -- number, string, boolean, etc
        copy = orig
    end
    return copy
end

function log(message, level)
    level = level or ngx.INFO
    ngx.log(level, message)
end

return {
    table_merge=table_merge,
    table_contains=table_contains,
    deepcopy=deepcopy,
    decode_referer=decode_referer,
    get_uri=get_uri,
    log=log,
}
