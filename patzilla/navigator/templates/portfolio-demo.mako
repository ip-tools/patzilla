<!DOCTYPE html>
<html>
    <head>
    </head>
    <!-- frameset is deprecated in html5, but it still works. -->
    <frameset framespacing="0" framepadding="0" cols="50%,50%" frameborder="1" nore3size="noresize" style="padding: 0px; margin: 0px">
        <frame name="opsbrowser_left_frame" src="/ops/browser?${request.query_string | n}" style="padding: 0px; margin: 0px"></frame>
        <frame name="opsbrowser_right_frame" style="padding: 0px; margin: 0px"></frame>
    </frameset>
</html>
