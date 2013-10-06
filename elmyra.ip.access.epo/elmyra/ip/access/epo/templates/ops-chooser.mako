<%inherit file="site.mako" />

<%block name="body">

## http://bootsnipp.com/snipps/e-mail-interface-like-gmail

<div class="container">

    <table class="table table-condensed table-hover">
      <thead>
        <tr>
          <th class="span1"><input type="checkbox"></th>
          <th class="span2">Patentnummer</th>
          <th class="span2">Info</th>
          <th class="span9">Bibliographische Daten</th>
          <th class="span2">Datum</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><input type="checkbox"> <a href="#"><i class="icon-star-empty"></i></a></td>
          <td><strong>John Doe</strong></td>
          <td><span class="label pull-right">Notifications</span></td>
          <td><strong>Message body goes here</strong></td>
          <td><strong>11:23 PM</strong></td>
        </tr>
        <tr>
          <td><input type="checkbox"> <a href="#"><i class="icon-star-empty"></i></a></td>
          <td>John Doe</td>
          <td><span class="label pull-right">Notifications</span></td>
          <td>Message body goes here</td>
          <td>Sept4</td>
        </tr>
        <tr>
          <td><input type="checkbox"> <a href="#"><i class="icon-star"></i></a></td>
          <td><strong>John Doe</strong></td>
          <td><span class="label pull-right">Notifications</span></td>
          <td><strong>Message body goes here</strong></td>
          <td><strong>Sept3</strong></td>
        </tr>
        <tr>
          <td><input type="checkbox"> <a href="#"><i class="icon-star"></i></a></td>
          <td><strong>John Doe</strong></td>
          <td><span class="label pull-right">Notifications</span></td>
          <td><strong>Message body goes here</strong></td>
          <td><strong>Sept3</strong></td>
        </tr>
      </tbody>
    </table>

</div>

</%block>
