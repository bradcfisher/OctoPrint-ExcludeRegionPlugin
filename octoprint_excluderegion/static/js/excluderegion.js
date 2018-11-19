$(function() {

// TODO: If isActivePrintJob state changes to printing while editing, the edit should be cancelled (notification to user when this happens?).

  var INSIDE = 1;
  var TOP    = 2;
  var BOTTOM = 4;
  var LEFT   = 8;
  var RIGHT  = 16;

  function RectangularRegion(x1, y1, x2, y2, id) {
    var self = this;

    self.type = "RectangularRegion";
    if (arguments.length == 1) {
      self.x1 = x1.x1;
      self.x2 = x1.x2;
      self.y1 = x1.y1;
      self.y2 = x1.y2;
      self.id = x1.id;
    } else {
      self.id = id;
      self.x1 = x1;
      self.x2 = x2;
      self.y1 = y1;
      self.y2 = y2;
    }

    self.normalizeX = function() {
      if (self.x1 > self.x2) {
        var x = self.x1;
        self.x1 = self.x2;
        self.x2 = x;
      }
    }

    self.normalizeY = function() {
      if (self.y1 > self.y2) {
        var y = self.y1;
        self.y1 = self.y2;
        self.y2 = y;
      }
    }

    // if range is 0 or not specified, will only detect if INSIDE or OUTSIDE
    self.pointNearRegion = function(pt, range) {
      range = Math.max(range, 0);

      self.normalizeX();
      self.normalizeY();

      var rval = (self.containsPoint(pt) ? INSIDE : 0);

      if (range) {
        var dx = self.x2 - self.x1;
        var dy = self.y2 - self.y1;

        var xrange = (dx < 2 * range ? dx / 2 : range);
        var yrange = (dy < 2 * range ? dy / 2 : range);

        if (rval || (
          (pt.x >= self.x1 - range) &&
          (pt.x <= self.x2 + range) &&
          (pt.y >= self.y1 - range) &&
          (pt.y <= self.y2 + range)
        )) {
          if (pt.x <= self.x1 + xrange) {
            rval |= LEFT;
          }

          if (pt.x > self.x2 - xrange) {
            rval |= RIGHT;
          }

          if (pt.y <= self.y1 + yrange) {
            rval |= TOP;
          }

          if (pt.y > self.y2 - yrange) {
            rval |= BOTTOM;
          }
        }
      }

      return rval;
    }
    
    self.containsPoint = function(pt) {
      self.normalizeX();
      if (pt.x < self.x1 || pt.x > self.x2) {
        return false;
      }

      self.normalizeY();
      if (pt.y < self.y1 || pt.y > self.y2) {
        return false;
      }

      return true;
    }

    self.renderPath = function(ctx, forStroke) {
      var x, w;
      if (self.x1 <= self.x2) {
        x = self.x1;
        w = self.x2 - x;
      } else {
        x = self.x2;
        w = self.x1 - x;
      }
      
      var y, h;
      if (self.y1 <= self.y2) {
        y = self.y1;
        h = self.y2 - y;
      } else {
        y = self.y2;
        h = self.y1 - y;
      }

      if (forStroke) {
        x += ctx.lineWidth / 2;
        y += ctx.lineWidth / 2;
        w -= ctx.lineWidth;
        h -= ctx.lineWidth;
      }

      ctx.moveTo(x, y);
      ctx.lineTo(x + w, y);
      ctx.lineTo(x + w, y + h);
      ctx.lineTo(x, y + h);
      ctx.closePath();
    }
  }

  function CircularRegion(cx, cy, r, id) {
    var self = this;

    self.type = "CircularRegion";
    if (arguments.length == 1) {
      self.id = cx.id;
      self.cx = cx.cx;
      self.cy = cx.cy;
      self.r = cx.r;
    } else {
      self.id = id;
      self.cx = cx;
      self.cy = cy;
      self.r = r;
    }

    // if range is 0 or not specified, will only detect if INSIDE or OUTSIDE
    self.pointNearRegion = function(pt, range) {
      range = Math.max(range, 0);

      var dx = pt.x - self.cx;
      var dy = pt.y - self.cy;

      var dist = Math.hypot(dx, dy);

      var rval = 0;
      if (dist <= self.r + range) {
        if (dist <= self.r) rval = INSIDE;

        if (range && (dist >= self.r - range)) {
          // Determine border piece by angle
          var border = [ RIGHT, BOTTOM | RIGHT, BOTTOM, BOTTOM | LEFT, LEFT, TOP | LEFT, TOP, TOP | RIGHT ];

          var twoPi = Math.PI * 2;
          var angle = Math.atan2(dy, dx);
          if (angle < 0)
            angle += twoPi;
          
          angle = (angle + Math.PI / 8) % twoPi;

          rval |= border[Math.floor(angle / (Math.PI / 4))];
        }
      }

      return rval;
    }

    self.containsPoint = function(pt) {
      return Math.hypot(self.cx - pt.x, self.cy - pt.y) <= self.r;
    }

    self.renderPath = function(ctx, forStroke) {
      var r = self.r;
      if (forStroke) r -= ctx.lineWidth / 2;
      if (r >= 0) {
        ctx.moveTo(self.cx + r, self.cy);
        ctx.arc(self.cx, self.cy, r, 0, Math.PI * 2);
        ctx.closePath();
      }
    }
  }

  function ExcludeRegionPluginViewModel(dependencies) {
    var self = this;

    self.gcodeViewModel = dependencies[0];
    self.loginState = dependencies[1];
    self.printerState = dependencies[2];
    self.global_settings = dependencies[3];
    self.touchui = dependencies[4];

    self.isFileSelected = ko.pureComputed(function() {
      return !!self.gcodeViewModel.selectedFile.path();
    });

    self.isFileSelected.subscribe(function() {
      enableExcludeButtons(self.isFileSelected());
    });

    self.isActivePrintJob = ko.pureComputed(function() {
      // Ensure all observables are called so dependency tracking works correctly
      var isPrinting = self.printerState.isPrinting();
      var isPausing = self.printerState.isPausing();
      var isPaused = self.printerState.isPaused();
      return isPrinting || isPaused || isPausing;
    });

    self.excludedRegions = ko.observableArray();

    function retrieveExcludeRegions() {
      OctoPrint.simpleApiGet("excluderegion").done(function(result) {
        self.excludedRegions(result.excluded_regions.map(cloneRegion));
      });
    }
    
    var $excludeRegionsOverlay = $('<canvas id="gcode_canvas_excludeRegions_overlay">');
    var $editRegionOverlay = $('<canvas id="gcode_canvas_editRegion_overlay">');

    var excludeRegionsOverlayContext = $excludeRegionsOverlay[0].getContext('2d');
    var editRegionOverlayContext = $editRegionOverlay[0].getContext('2d');

    var excludeRegionsOverlay_renderStroke = false;
    var selectedRegion = null;
    var originalRegion = null;
    var selectedRegionType = null;
    var editMode = null;  // first|size|adjust-new|adjust|select

/*    
    var $outputOverlay = $('<div id="gcode_output_overlay">');
    function overlayOutput(content) {
      $outputOverlay.html(content);
    }
*/

    function cloneRegion(region) {
      switch (region.type) {
        case "RectangularRegion":
          return new RectangularRegion(region);
          break;

        case "CircularRegion":
          return new CircularRegion(region);
          break;
          
        default:
          console.log("Unexpected region type:", region);
      }
    }

    var pixelRatio = window.devicePixelRatio || 1;
    function eventPositionToCanvasPt(event) {
      var canvas = $excludeRegionsOverlay[0];
      var x = (event.offsetX !== undefined ? event.offsetX : (event.pageX - canvas.offsetLeft));
      var y = (event.offsetY !== undefined ? event.offsetY : (event.pageY - canvas.offsetTop));
      var pt = transformedPoint(x * pixelRatio, y * pixelRatio);

      /*
      overlayOutput(
        "pixelRatio: "+ pixelRatio +"<br>\n"+
        "event: x="+ x * pixelRatio +", y="+ y * pixelRatio +"<br>\n"+
        "result: x="+ pt.x +", y="+ pt.y
      );
      */

      return pt;
    }

    // Finds a region containing the specified point
    // Regions are searched in reverse creation order, and the first region found is returned.
    function regionUnderPoint(pt) {
      var regions = self.excludedRegions();
      for (var i = regions.length - 1; i >= 0; i--) {
        if (regions[i].containsPoint(pt)) {
          return regions[i];
        }
      }
    }

    // Finds a region near the specified point
    // Regions are searched in reverse creation order, and the first region found is returned.
    function regionNearPoint(pt, range) {
      range = Math.max(range || 5, 0);

      var regions = self.excludedRegions();
      for (var i = regions.length - 1; i >= 0; i--) {
        var near = regions[i].pointNearRegion(pt, range);
        console.log("regionNearPoint: region=", regions[i], "near=", near);
        if (near) {
          return [regions[i], near];
        }
      }
    }

    // Updates the mouse cursor when modifying a region
    function handleAdjustMouseHover(e) {
      var pt = eventPositionToCanvasPt(e);
      updateCursor(selectedRegion, pt, (editMode == "adjust-new"));
    }

    // Updates the mouse cursor to indicate what action (move, resize, none) can be taken for a
    // given region based on the specified point.
    function updateCursor(region, pt, allowMove) {
      var near = region.pointNearRegion(pt, 5);

      var $gcodeCanvas = $("#gcode_canvas");
      var cursor = "default";

      if (near & LEFT) {
        if (near & TOP) {
          cursor = "nesw-resize";
        } else if (near & BOTTOM) {
          cursor = "nwse-resize";
        } else {
          cursor = "ew-resize";
        }
      } else if (near & RIGHT) {
        if (near & TOP) {
          cursor = "nwse-resize";
        } else if (near & BOTTOM) {
          cursor = "nesw-resize";
        } else {
          cursor = "ew-resize";
        }
      } else if ((near & TOP) || (near & BOTTOM)) {
        cursor = "ns-resize";
      } else if ((near == INSIDE) && allowMove) {
        cursor = "move"
      }

      $gcodeCanvas.css({"cursor": cursor});
    }

    // Highlights the region the mouse is over and updates the mouse cursor when in select mode
    function handleSelectMouseHover(e) {
      var pt = eventPositionToCanvasPt(e);
      var region = regionUnderPoint(pt);

      if (handleSelectMouseHover.lastRegion != region) {
        handleSelectMouseHover.lastRegion = region;

        originalRegion = region;
        selectedRegion = (region != null ? cloneRegion(region) : null);
        renderEditRegionOverlay();

        var cursor = (region ? "grab" : "default");
        console.log("handleSelectMouseHover: set cursor=", cursor);
        $("#gcode_canvas").css({"cursor": cursor});
      }
    }

    // Selects the region under the mouse cursor when the user starts to drag the canvas
    function captureDragStartEventSelect(pt) {
      console.log("captureDragStartEventSelect: pt=", pt);

      // Select the region under the point, if any
      selectedRegion = regionUnderPoint(pt);

      // If a region is selected, then change the state to adjust mode
      if (selectedRegion != null) {
        $("#gcode_canvas").off("mousemove", handleSelectMouseHover);
        originalRegion = selectedRegion;
        selectedRegion = cloneRegion(selectedRegion);
        beginEditMode(selectedRegion, "adjust");
        return false;
      }
    }

    // Creates a new region at the specified point and starts capturing mouse events
    // when the user starts to drag the canvas
    function captureDragStartEventCreate(pt) {
      originalRegion = null;

      // Create a new region locally and prevent the default action
      if (selectedRegionType == "RectangularRegion") {
        selectedRegion = new RectangularRegion(pt.x, pt.y, pt.x, pt.y);
      } else if (selectedRegionType == "CircularRegion") {
        selectedRegion = new CircularRegion(pt.x, pt.y, 0);
      } else {
        throw new ArgumentError("Unsupported selectedRegionType: "+ selectedRegionType);
      }
      renderEditRegionOverlay();

      // Remove hook for drag start event
      GCODE.renderer.setOption({
        "onDragStart" : null
      });

      var $gcodeCanvas = $("#gcode_canvas");

      var mouseMoveHandler = function(e) {
        var pt = eventPositionToCanvasPt(e);
        if (selectedRegion instanceof RectangularRegion) {
          selectedRegion.x2 = pt.x;
          selectedRegion.y2 = pt.y;
        } else if (selectedRegion instanceof CircularRegion) {
          selectedRegion.r = Math.hypot(
            pt.x - selectedRegion.cx,
            pt.y - selectedRegion.cy
          );
        }

        renderEditRegionOverlay();
      };

      var mouseUpHandler = function(e) {
        $gcodeCanvas.off("mousemove", mouseMoveHandler);
        $gcodeCanvas.off("mouseup", mouseUpHandler);

        beginEditMode(selectedRegion, "adjust-new");
      }

      $gcodeCanvas.on("mousemove", mouseMoveHandler);
      $gcodeCanvas.on("mouseup", mouseUpHandler);

      beginEditMode(selectedRegion, "size");

      return false;
    }
    
    function captureDragStartEventSize(startPt) {
      console.log("captureDragStartEventSize: pt=", startPt);
      var near = selectedRegion.pointNearRegion(startPt, 5);
      
      var isNewOrNotPrinting = (editMode == "adjust-new");

      updateCursor(selectedRegion, startPt, isNewOrNotPrinting);

      if (!near || (!isNewOrNotPrinting && (near == INSIDE)))
        return;

      var $gcodeCanvas = $("#gcode_canvas");

      var mouseMoveHandler;
      if (near == INSIDE) {
        var x1 = selectedRegion.x1;
        var x2 = selectedRegion.x2;
        var y1 = selectedRegion.y1;
        var y2 = selectedRegion.y2;
        var cx = selectedRegion.cx;
        var cy = selectedRegion.cy;

        // Reposition
        mouseMoveHandler = function(e) {
          var pt = eventPositionToCanvasPt(e);
          var dx = pt.x - startPt.x;
          var dy = pt.y - startPt.y;

          if (selectedRegion instanceof RectangularRegion) {
            selectedRegion.x1 = x1 + dx;
            selectedRegion.x2 = x2 + dx;
            selectedRegion.y1 = y1 + dy;
            selectedRegion.y2 = y2 + dy;
          } else if (selectedRegion instanceof CircularRegion) {
            selectedRegion.cx = cx + dx;
            selectedRegion.cy = cy + dy;
          } else {
            throw new ArgumentError("Unsupported selectedRegionType: "+ selectedRegionType);
          }

          renderEditRegionOverlay();
        }
      } else {
        // Resize
        mouseMoveHandler = function(e) {
          var pt = eventPositionToCanvasPt(e);

          if (selectedRegion instanceof RectangularRegion) {
            // Compute new edge position
            var x1 = originalRegion.x1;
            var x2 = originalRegion.x2;
            var y1 = originalRegion.y1;
            var y2 = originalRegion.y2;

            if (near & LEFT) {
              selectedRegion.x1 = (isNewOrNotPrinting || pt.x <= x1 ? pt.x : x1);
            } else if (near & RIGHT) {
              selectedRegion.x2 = (isNewOrNotPrinting || pt.x >= x2 ? pt.x : x2);
            }

            if (near & TOP) {
              selectedRegion.y1 = (isNewOrNotPrinting || pt.y <= y1 ? pt.y : y1);
            } else if (near & BOTTOM) {
              selectedRegion.y2 = (isNewOrNotPrinting || pt.y >= y2 ? pt.y : y2);
            }
          } else if (selectedRegion instanceof CircularRegion) {
            // Compute new size
            var r = Math.hypot(pt.x - selectedRegion.cx, pt.y - selectedRegion.cy);
            if (!isNewOrNotPrinting)
              r = Math.max(r, originalRegion.r);

            selectedRegion.r = r;
          } else {
            throw new ArgumentError("Unsupported selectedRegionType: "+ selectedRegionType);
          }

          renderEditRegionOverlay();
        }
      }

      var mouseUpHandler = function(e) {
        $gcodeCanvas.off("mousemove", mouseMoveHandler);
        $gcodeCanvas.off("mouseup", mouseUpHandler);

        $gcodeCanvas.on("mousemove", handleAdjustMouseHover);
      }

      $gcodeCanvas.on("mousemove", mouseMoveHandler);
      $gcodeCanvas.on("mouseup", mouseUpHandler);
      
      return false;
    }
    
    function endEditMode() {
      if (beginEditMode.lastSelector) {
        $(beginEditMode.lastSelector).hide();
        $("#gcode_exclude_controls .main").show();
        delete beginEditMode.lastSelector;
        originalRegion = null;
        selectedRegion = null;
        selectedRegionType = null;
        editMode = null;

        // Remove hook for drag start event
        GCODE.renderer.setOption({
          "onDragStart" : null
        });
       
        // Remove handler for mouse move event
        var $gcodeCanvas = $("#gcode_canvas");
        $gcodeCanvas.off("mousemove", handleSelectMouseHover);
        $gcodeCanvas.off("mousemove", handleAdjustMouseHover);

        renderExcludeRegionsOverlay(false);
      }
    }

    function beginEditMode(regionOrType, messageType) {
      editMode = messageType;
      if ((editMode == "adjust") && !self.isActivePrintJob()) {
        editMode = "adjust-new";
      }

      if (regionOrType.type) {
        originalRegion = regionOrType;
        selectedRegion = cloneRegion(regionOrType);
        selectedRegionType = regionOrType.type;
      } else {
        originalRegion = null;
        selectedRegion = null;
        selectedRegionType = regionOrType;
      }

      if (beginEditMode.lastSelector) {
        $(beginEditMode.lastSelector).hide();
      } else {
        $("#gcode_exclude_controls .main").hide();
      }

      var msgSel = "#gcode_exclude_controls .message";
      var rgnSel = msgSel +" ."+ selectedRegionType;
      sel = msgSel +","+ rgnSel +","+ rgnSel +" .text."+ messageType;

      $(sel).show();

      beginEditMode.lastSelector = sel;

      // Add hook to capture drag start event
      var $gcodeCanvas = $("#gcode_canvas");
      $gcodeCanvas.off("mousemove", handleSelectMouseHover);
      $gcodeCanvas.off("mousemove", handleAdjustMouseHover);

      var $acceptButton = $("#gcode_exclude_controls .message .action-buttons .btn.accept");
      $acceptButton.addClass("disabled");

      var $deleteButton = $("#gcode_exclude_controls .message .action-buttons .btn.delete");
      $deleteButton.addClass("disabled");
      $deleteButton.hide();

      var onDragStart;
      switch (editMode) {
        case "first":
          onDragStart = captureDragStartEventCreate;
          break;
        case "size":
          break;
        case "select":
          onDragStart = captureDragStartEventSelect;
          renderExcludeRegionsOverlay(true);
          $gcodeCanvas.on("mousemove", handleSelectMouseHover);
          if (!self.isActivePrintJob()) {
            $deleteButton.show();
          }
          break;
        case "adjust":
        case "adjust-new":
          onDragStart = captureDragStartEventSize;
          renderExcludeRegionsOverlay(true);
          $gcodeCanvas.on("mousemove", handleAdjustMouseHover);
          $acceptButton.removeClass("disabled");
          if ((messageType != "adjust-new") && !self.isActivePrintJob()) {
            $deleteButton.show();
            $deleteButton.removeClass("disabled");
          }
          break;
      }

      GCODE.renderer.setOption({
        "onDragStart" : onDragStart
      });
    }
    
    function beginSelectMode() {
      beginEditMode("modifyRegion", "select");
    }

    function commitEdits(action) {
      var command = (selectedRegion.id
            ? (action == "delete" ? "deleteExcludeRegion" : "updateExcludeRegion")
            : "addExcludeRegion");

      OctoPrint.simpleApiCommand("excluderegion", command, selectedRegion).done(function(result) {
        console.log("ExcludeRegionPlugin::executed "+ command +" via REST API:", result);
        endEditMode();
      });
    }
    
    function cloneNodeSize(fromNode, toNode) {
      toNode.style.height = fromNode.style.height || fromNode.width+"px";
      toNode.style.width = fromNode.style.width || fromNode.height+"px";
      if ((toNode.width !== undefined) && (fromNode.width !== undefined)) {
        toNode.width = fromNode.width;
        toNode.height = fromNode.height;
      }
    }
    
    function appendOverlay($parent, $overlay, $canvas) {
      $parent.append($overlay);
      cloneNodeSize($canvas[0], $overlay[0]);
    }

    function addCanvasOverlays() {
      if ($("#canvas_container").find(".gcode_canvas_wrapper").length == 0) {
        var $gcodeCanvas = $("#gcode_canvas");
        
        var $wrapper = $('<div class="gcode_canvas_wrapper"></div>');
        $gcodeCanvas[0].parentNode.insertBefore($wrapper[0], $gcodeCanvas[0]);
        $wrapper.append($gcodeCanvas);
        cloneNodeSize($gcodeCanvas[0], $wrapper[0]);

        appendOverlay($wrapper, $excludeRegionsOverlay, $gcodeCanvas);
        appendOverlay($wrapper, $editRegionOverlay, $gcodeCanvas);
        //appendOverlay($wrapper, $outputOverlay, $gcodeCanvas);
      }
    }
    
    function addExcludeButtons() {
      // Don't create buttons if using TouchUI, since they don't work anyway
      if (self.touchui && self.touchui.isActive())
        return;
      
      if (!$("#gcode_exclude_controls").length) {
        $("#canvas_container").after(
          '<div id="gcode_exclude_controls">'+
            '<div class="main">'+
              gettext("Print Exclusion Regions")+
              ' <div class="btn-group action-buttons">'+
                '<div class="btn btn-mini disabled excludeRectangle" title="'+ gettext("Add a new rectangular print exclusion region") +'">'+
                  '<i class="fa fa-times-rectangle-o"></i>'+ gettext("Add Rectangle") +'</div>'+
                '<div class="btn btn-mini disabled excludeCircle" title="'+ gettext("Add a new circular print exclusion region") +'">'+
                  '<i class="fa fa-times-circle-o"></i>'+ gettext("Add Circle") +'</div>'+
                '<div class="btn btn-mini disabled modifyRegion" title="'+ gettext("Modify an existing region") +'">'+
                  '<i class="fa fa-edit"></i>'+ gettext("Modify Region") +'</div>'+
              '</div>'+
            '</div>'+
            '<div class="message">'+
              '<span class="region RectangularRegion">'+
                '<div class="label"><i class="fa fa-times-rectangle-o"></i>'+ gettext("Rectangle") +'</div>'+
                '<span class="text first">'+
                  '<i class="fa fa-crosshairs"></i>'+ gettext("Click to set first corner")+
                '</span>'+
                '<span class="text size">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag to adjust size")+
                '</span>'+
                '<span class="text adjust-new">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag interior to reposition or border to resize")+
                '</span>'+
                '<span class="text adjust">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag border to resize")+
                '</span>'+
              '</span>'+
              '<span class="region CircularRegion">'+
                '<div class="label"><i class="fa fa-times-circle-o"></i>'+ gettext("Circle") +'</div>'+
                '<span class="text first">'+
                  '<i class="fa fa-dot-circle-o"></i>'+ gettext("Click to set center point")+
                '</span>'+
                '<span class="text size">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag to adjust size")+
                '</span>'+
                '<span class="text adjust-new">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag interior to reposition or border to resize")+
                '</span>'+
                '<span class="text adjust">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag border to resize")+
                '</span>'+
              '</span>'+
              '<span class="region modifyRegion">'+
                '<div class="label"><i class="fa fa-edit"></i>'+ gettext("Modify Region") +'</div>'+
                '<span class="text select">'+
                  '<i class="fa fa-hand-pointer-o"></i>'+ gettext("Click to select the region to modify")+
                '</span>'+
              '</span>'+
              '<div class="btn-group action-buttons">'+
                '<div class="btn btn-mini cancel"><i class="fa fa-ban"></i>'+ gettext("Cancel") +'</div>'+
                '<div class="btn btn-mini delete"><i class="fa fa-trash-o"></i>'+ gettext("Delete") +'</div>'+
                '<div class="btn btn-mini accept"><i class="fa fa-check"></i>'+ gettext("Accept") +'</div>'+
              '</div>'+
            '</div>'+
          '</div>'
        );

        // Check if user isn't logged in
        if (!self.loginState.loggedIn()) {
            // Disable edit buttons
            $("#gcode_exclude_controls button").addClass("disabled");
        }

        // Edit button click event
        self.$excludeButtons = $("#gcode_exclude_controls .btn");

        self.$excludeButtons.click(function() {
          var $button = $(this);

          // Blur self
          $button.blur();

          // Check if button is not disabled
          if (!$button.hasClass("disabled")) {
            if ($button.hasClass("excludeRectangle")) {
              beginEditMode("RectangularRegion", "first");
            } else if ($button.hasClass("excludeCircle")) {
              beginEditMode("CircularRegion", "first");
            } else if ($button.hasClass("modifyRegion")) {
              beginSelectMode();
            } else if ($button.hasClass("cancel")) {
              endEditMode();
            } else if ($button.hasClass("accept")) {
              commitEdits();
            } else if ($button.hasClass("delete")) {
                showConfirmationDialog({
                    message: gettext("This will remove the selected region."),
                    onproceed: function() {
                      commitEdits("delete");
                    }
                });
            }
          }
        });

        enableExcludeButtons(self.isFileSelected());
      }
    }

    function addExcludeRegion(region) {
      OctoPrint.simpleApiCommand("excluderegion", "addExcludeRegion", region);
    }

    function removeExcludeButtons() {
      $("#gcode_exclude_controls").remove();
      delete self.$excludeButtons;
    }

    function enableExcludeButtons(enabled) {
      if (self.$excludeButtons) {
        if (enabled) {
          if (self.excludedRegions().length > 0) {
            self.$excludeButtons.removeClass("disabled");
          } else {
            self.$excludeButtons.not(".modifyRegion").removeClass("disabled");
            self.$excludeButtons.filter(".modifyRegion").addClass("disabled");
          }
        } else {
          self.$excludeButtons.addClass("disabled");
        }
      }
    }

    self.onServerReconnect = function() {
      retrieveExcludeRegions();
    }

    self.onBeforeBinding = function() {
      self.settings = self.global_settings.settings.plugins.excluderegion;
      console.log("onBeforeBinding: settings=", self.settings);
      self.onEventSettingsUpdated();
    }

    self.onEventSettingsUpdated = function() {
      console.log("onEventSettingsUpdated: settings=", self.settings);

// TODO: This sorting should either happen _before_ saving (would that need to be in the python code?)
      self.extendedExcludeGcodes = self.settings.extendedExcludeGcodes.sort(
        function(a, b) {
          var uca = a.gcode().toLocaleUpperCase();
          var ucb = b.gcode().toLocaleUpperCase();
          if (uca < ucb)
            return -1;
          if (uca > ucb)
            return 1;
          return 0;
        }
      );
    }

    self.addExtendedGcode = function() {
      var $gcode = $("#settings-excluderegion_newExtendedGcode");
      var gcode = $gcode.val().trim();

      var $mode = $("#settings-excluderegion_newExtendedGcodeMode");
      var mode = $mode.val();

      var $desc = $("#settings-excluderegion_newExtendedGcodeDescription");
      var desc = $desc.val();

      self.settings.extendedExcludeGcodes.push({
        "gcode": ko.observable(gcode),
        "mode": ko.observable(mode),
        "description": ko.observable(desc)
      });

      $gcode.val('');
      $mode.val('exclude');
      $desc.val('');
    }
    
    self.removeExtendedGcode = function(row) {
      self.settings.extendedExcludeGcodes.remove(row);
    }
    
    function resetExcludeButtons() {
      removeExcludeButtons();
      addExcludeButtons();
    }

    if (self.touchui) {
      self.touchui.isActive.subscribe(resetExcludeButtons);
    }
    self.onSettingsHidden = resetExcludeButtons;
    self.onUserLoggedIn = resetExcludeButtons;

    self.onUserLoggedOut = function() {
      removeExcludeButtons();
    }

    function handleExcludedRegionsChanged(regions) {
      self.excludedRegions(regions.map(cloneRegion));
    }

    self.onDataUpdaterPluginMessage = function(plugin, data) {
      if (plugin == "excluderegion") {
        switch (data.event) {
          case "ExcludedRegionsChanged":
            handleExcludedRegionsChanged(data.excluded_regions);
            break;
        }
      }
    }

    var renderFrameCallbacks;
    function renderFrame(id, callback /*, ...args */) {
      if (renderFrameCallbacks == null) {
        renderFrameCallbacks = {};

        requestAnimationFrame(function() {
          var callbacks = renderFrameCallbacks;
          renderFrameCallbacks = null;

          for (var id in callbacks) {
            var cb = callbacks[id];
            cb[0].apply(null, cb[1]);
          }
        });
      }

      if (!renderFrameCallbacks[id]) {
        renderFrameCallbacks[id] = [ callback, Array.prototype.slice.call(arguments, 2) ];
      }
    }

    function clearContext(ctx) {
      var p1 = transformedPoint(0, 0);
      var p2 = transformedPoint(ctx.canvas.width, ctx.canvas.height);
      ctx.clearRect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y);
    }

    function renderEditRegionOverlay_callback() {
      var ctx = editRegionOverlayContext;
      ctx.save();

      clearContext(ctx);

      if (selectedRegion != null) {
        ctx.globalAlpha = 0.5;
        ctx.fillStyle = "orange";
        ctx.lineWidth = 1.0;
        ctx.strokeStyle = "black";

        ctx.beginPath();
        selectedRegion.renderPath(ctx);
        ctx.fill();

        ctx.beginPath();
        selectedRegion.renderPath(ctx, true);
        ctx.stroke();
      }

      ctx.restore();
    }

    function renderExcludeRegionsOverlay_callback() {
      var ctx = excludeRegionsOverlayContext;
      ctx.save();

      clearContext(ctx);

      ctx.globalAlpha = 0.5;
      ctx.fillStyle = "red";
      ctx.lineWidth = 1.0;
      ctx.strokeStyle = GCODE.renderer.getOptions().colorGrid;

      var regions = self.excludedRegions();
      var selRegion;

      ctx.beginPath();
      for (var i = regions.length - 1; i >= 0; --i) {
        if (selectedRegion && (regions[i].id == selectedRegion.id)) {
          selRegion = regions[i];
        } else {
          regions[i].renderPath(ctx);
        }
      }
      ctx.fill();

      if (selRegion) {
        ctx.fillStyle = ctx.strokeStyle;
        ctx.beginPath();
        selRegion.renderPath(ctx);
        ctx.fill();
      }
      
      if (excludeRegionsOverlay_renderStroke) {
        ctx.beginPath();
        for (var i = regions.length - 1; i >= 0; --i) {
          regions[i].renderPath(ctx, true);
        }
        ctx.stroke();
      }

      ctx.restore();
    }
    
    function renderEditRegionOverlay() {
      renderFrame("editRegionOverlay", renderEditRegionOverlay_callback);
    }
    
    function renderExcludeRegionsOverlay(renderStroke) {
      if (renderStroke != undefined)
        excludeRegionsOverlay_renderStroke = renderStroke;

      renderFrame("excludeRegionsOverlay", renderExcludeRegionsOverlay_callback);
    }

    var svg = document.createElementNS("http://www.w3.org/2000/svg",'svg');
    var pt  = svg.createSVGPoint();
    overlayXform = svg.createSVGMatrix();
    function transformedPoint(x,y) {
        pt.x=x; pt.y=y;
        return pt.matrixTransform(overlayXform.inverse());
    }

    var startupComplete = false;
    var gcodeViewerPollingComplete = false;

    self.onStartupComplete = function() {
      addCanvasOverlays();
      retrieveExcludeRegions();

      startupComplete = true;
      initializeControlsIfReady();
    }

    function initializeControlsIfReady() {
      if (startupComplete && gcodeViewerPollingComplete) {
        if (self.loginState.loggedIn()) {
          addExcludeButtons();
        }
      }
    }

    var gcodeViewerPollFn = function() {
      if (!GCODE || !GCODE.renderer || !GCODE.renderer.getOptions().hasOwnProperty('onViewportChange')) {
        setTimeout(gcodeViewerPollFn, 10);
        return;
      }

      // Hook into the GCODE viewer to render the exclude regions
      GCODE.renderer.setOption({
        onViewportChange: function(xform) {
          overlayXform = xform;
          excludeRegionsOverlayContext.setTransform(xform.a, xform.b, xform.c, xform.d, xform.e, xform.f);
          editRegionOverlayContext.setTransform(xform.a, xform.b, xform.c, xform.d, xform.e, xform.f);
          renderExcludeRegionsOverlay();
          renderEditRegionOverlay();
        },
/*
        onDragStart: function(pt) {
          console.log("ExcludeRegionPlugin:: GCODE onDragStart called:", pt);
        },
        onDrag: function(pt) {
          console.log("ExcludeRegionPlugin:: GCODE onDrag called:", pt);
        },
        onDragStop: function(pt) {
          console.log("ExcludeRegionPlugin:: GCODE onDragStop called:", pt);
        }
*/
      });

      self.excludedRegions.subscribe(function() {
        console.log("ExcludeRegionPlugin:: excludedRegions updated, redrawing GCODE viewer: excludedRegions=", self.excludedRegions());

        endEditMode();
        enableExcludeButtons(self.isFileSelected());

        try {
          renderExcludeRegionsOverlay();
        } catch (e) {
          console.log("GCODE refresh failed:", e);
        }
      });

      gcodeViewerPollingComplete = true;
      initializeControlsIfReady();
    };
    gcodeViewerPollFn();
  }

  OCTOPRINT_VIEWMODELS.push({
    "construct": ExcludeRegionPluginViewModel,
    "dependencies": ["gcodeViewModel", "loginStateViewModel", "printerStateViewModel", "settingsViewModel", "touchUIViewModel"],
    "optional": ["touchUIViewModel"],
    "elements": ["#settings_plugin_excluderegion"]
  });

});