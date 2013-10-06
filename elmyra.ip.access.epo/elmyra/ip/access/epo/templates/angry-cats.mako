<%inherit file="site.mako" />

<%block name="body">

<link rel="stylesheet" type="text/css" href="/static/css/angry-cats.css" />
<script type="text/javascript" src="/static/js/angry-cats.js"></script>

## http://davidsulc.com/blog/2012/04/15/a-simple-backbone-marionette-tutorial/
## https://github.com/davidsulc/backbone.marionette-collection-example

<div id="content">
</div>

<%text>
    <script type="text/template" id="angry_cats-template">
      <thead>
        <tr class='header'>
          <th>Rank</th>
          <th>Votes</th>
          <th>Name</th>
          <th>Image</th>
          <th></th>
          <th></th>
        </tr>
      </thead>
      <tbody>
      </tbody>
    </script>
</%text>

<%text>
    <script type="text/template" id="angry_cat-template">
      <td><%= rank %></td>
      <td><%= votes %></td>
      <td><%= name %></td>
      <td><img class='angry_cat_pic' src='<%= image_path %>' /></td>
      <td>
        <div class='rank_up'><img src='/static/img/angry-cats/up.gif' /></div>
        <div class='rank_down'><img src='/static/img/angry-cats/down.gif' /></div>
      </td>
      <td><a href="#" class="disqualify">Disqualify</a></td>
    </script>
</%text>

</%block>
