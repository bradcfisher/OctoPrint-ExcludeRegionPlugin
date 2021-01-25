$(function() {

  var BASE_BORDER_RANGE = 5;

  var RENDER_REGION_ALPHA = 0.5;
  var RENDER_BORDER_WIDTH = 3.0;
  var RENDER_FILL_SELECTED = "orange";
  var RENDER_STROKE_SELECTED = "black";
  var RENDER_FILL_NORMAL = "red";
  var RENDER_STROKE_NORMAL = "gray";

  var INSIDE = 1;
  var TOP    = 2;
  var BOTTOM = 4;
  var LEFT   = 8;
  var RIGHT  = 16;
  
  function Layer(number, height) {
    var self = this;
    if (arguments.length == 1) {
      self.number = number.number;
      self.height = number.height;
    } else {
      self.number = number;
      self.height = height;
    }
  }
  
  function Region(type, minLayer, maxLayer, id) {
    var self = this;

    self.type = type;
    self.id = id;
    self.minLayer = minLayer ? new Layer(minLayer) : null;
    self.maxLayer = maxLayer ? new Layer(maxLayer) : null;

    self.getMinHeight = function() {
      return (self.minLayer ? self.minLayer.height : 0);
    }

    self.getMaxHeight = function() {
      return (self.maxLayer ? self.maxLayer.height : null);
    }

    self.inHeightRange = function(z) {
      var max = self.getMaxHeight();
      return (self.getMinHeight() <= z) && (!max || (max >= z));
    }
  }

  function RectangularRegion(x1, y1, x2, y2, minLayer, maxLayer, id) {
    var self = this;

    if (arguments.length == 1) {
      Region.call(self, "RectangularRegion", x1.minLayer, x1.maxLayer, x1.id);
      self.x1 = x1.x1;
      self.x2 = x1.x2;
      self.y1 = x1.y1;
      self.y2 = x1.y2;
    } else {
      Region.call(self, "RectangularRegion", minLayer, maxLayer, id);
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
    
    self.getBounds = function() {
      self.normalizeX();
      self.normalizeY();
      return { x1: self.x1, y1: self.y1, x2: self.x2, y2: self.y2 };
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
  RectangularRegion.prototype = new Region();
  Object.defineProperty(RectangularRegion.prototype, 'constructor', {
    value: RectangularRegion,
    enumerable: false,
    writable: true });
  self.RectangularRegion = RectangularRegion;

  function CircularRegion(cx, cy, r, minLayer, maxLayer, id) {
    var self = this;

    if (arguments.length == 1) {
      Region.call(self, "CircularRegion", cx.minLayer, cx.maxLayer, cx.id);
      self.cx = cx.cx;
      self.cy = cx.cy;
      self.r = cx.r;
    } else {
      Region.call(self, "CircularRegion", minLayer, maxLayer, id);
      self.cx = cx;
      self.cy = cy;
      self.r = r;
    }

    self.getBounds = function() {
      return {
        x1: self.cx - self.r, y1: self.cy - self.r,
        x2: self.cx + self.r, y2: self.cy + self.r
      };
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
  CircularRegion.prototype = new Region();
  Object.defineProperty(CircularRegion.prototype, 'constructor', {
    value: CircularRegion,
    enumerable: false,
    writable: true });
  self.CircularRegion = CircularRegion;

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

    self.isEditingLimited = ko.pureComputed(function() {
      // Ensure all observables are called so dependency tracking works correctly
      var isPrinting = self.printerState.isPrinting();
      var isPausing = self.printerState.isPausing();
      var isPaused = self.printerState.isPaused();
      var mayShrinkRegionsWhilePrinting = self.settings.mayShrinkRegionsWhilePrinting();
      return (isPrinting || isPaused || isPausing) && !mayShrinkRegionsWhilePrinting;
    });

    self.excludedRegions = ko.observableArray();
    
    self.currentLayer = ko.observable();

    function retrieveExcludeRegions() {
      OctoPrint.simpleApiGet("excluderegion").done(function(result) {
        self.excludedRegions(result.excluded_regions.map(cloneRegion));
      });
    }
    
    var $excludeRegionsOverlay = $('<canvas id="gcode_canvas_excludeRegions_overlay">');
    var $editRegionOverlay = $('<canvas id="gcode_canvas_editRegion_overlay">');
    $editRegionOverlay.tooltip({
      trigger: "manual",
      placement: "top-start",
      animation: false,
      title: function() {
        var min = selectedRegion.getMinHeight();
        var max = selectedRegion.getMaxHeight();
        console.log("tooltip title: min=", min, "max=", max, "selectedRegion=", selectedRegion);
        return "Z range: " + min + "mm to " + (max ? max +"mm" : "Infinity");
      }
    });

    var excludeRegionsOverlayContext = $excludeRegionsOverlay[0].getContext('2d');
    var editRegionOverlayContext = $editRegionOverlay[0].getContext('2d');

    var excludeRegionsOverlay_renderStroke = false;
    var selectedRegion = null;
    var selectedRegionType = null;
    var editMode = null;  // new|size|adjust|adjust-limited|select

/*    
    var $outputOverlay = $('<div id="gcode_output_overlay">');
    function overlayOutput(content) {
      $outputOverlay.html(content);
    }
*/

    function cloneRegion(region) {
      var clone;
      switch (region.type) {
        case "RectangularRegion":
          clone = new RectangularRegion(region);
          break;

        case "CircularRegion":
          clone = new CircularRegion(region);
          break;
          
        default:
          console.log("Unexpected region type:", region);
          return null;
      }
      
      if (region instanceof Region) {
        clone.relatedRegion = region.relatedRegion || region;
      }
      
      return clone;
    }

    var pixelRatio = window.devicePixelRatio || 1;
    function eventPositionToCanvasPt(event) {
      var canvas = $excludeRegionsOverlay[0];
      var x = (event.offsetX !== undefined ? event.offsetX : (event.pageX - canvas.offsetLeft));
      var y = (event.offsetY !== undefined ? event.offsetY : (event.pageY - canvas.offsetTop));
      var pt = transformViewToDrawing(x * pixelRatio, y * pixelRatio);

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
        //console.log("regionUnderPoint: pt=", pt, "contains=", regions[i].containsPoint(pt), "region=", regions[i]);
        if (regions[i].containsPoint(pt)) {
          return regions[i];
        }
      }
    }

    // Finds a region near the specified point
    // Regions are searched in reverse creation order, and the first region found is returned.
    function regionNearPoint(pt, range) {
      range = Math.max(range || BASE_BORDER_RANGE / viewportScale, 0);

      var regions = self.excludedRegions();
      for (var i = regions.length - 1; i >= 0; i--) {
        var near = regions[i].pointNearRegion(pt, range);
        //console.log("regionNearPoint: region=", regions[i], "near=", near);
        if (near) {
          return [regions[i], near];
        }
      }
    }

    // Updates the mouse cursor when the mouse position changes while modifying a region
    function handleAdjustMouseHover(e) {
      var pt = eventPositionToCanvasPt(e);
      updateCursor(selectedRegion, pt, (editMode == "adjust"));
    }

    var viewportScale = 1;
    function updateViewportScale() {
      var p = transformViewToDrawing(0,0);
      var x = p.x;
      var y = p.y;
      p = transformViewToDrawing(pixelRatio,0);
      x -= p.x;
      y -= p.y;
      viewportScale = 1 / Math.hypot(x, y);
    }

    // Updates the mouse cursor to indicate what action (move, resize, none) can be taken for a
    // given region based on the specified point.
    function updateCursor(region, pt, allowMove) {
      var near = region.pointNearRegion(pt, BASE_BORDER_RANGE / viewportScale);

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

    // Selects the specified region & returns the edit overlay clone
    self.selectRegion = function(region, retainIfNull) {
      //console.log("selectRegion(region=", region, ", retainIfNull=", retainIfNull, ")");
      
      if ((region != null) || !retainIfNull) {
        region = (region != null ? region.relatedRegion || region : null);
        
        var relatedRegion = (selectedRegion != null ? selectedRegion.relatedRegion || selectedRegion : null);
        if (region != relatedRegion) {
          // If a region is selected, then update the internal selection state
          if (region != null) {
            if (self.excludedRegions().indexOf(region) != -1) {
              //console.log("selectRegion: region is registered, creating clone");
              region = cloneRegion(region);
            }
            selectedRegion = region;
            selectedRegionType = region.type;
            
            $editRegionOverlay.tooltip('show');
          } else {
            selectedRegion = null;
            selectedRegionType = null;
            
            $editRegionOverlay.tooltip('hide');
          }
        }
        
        renderEditRegionOverlay();
      }

      //console.log("selectRegion: DONE: selectedRegion=", selectedRegion, ", selectedRegionType=", selectedRegionType);

      return selectedRegion;
    };

    // Selects the region under the point, if any, and returns the overlay clone
    self.selectRegionUnderPoint = function(point, retainIfNotFound) {
      return self.selectRegion(regionUnderPoint(point), retainIfNotFound);
    };

    function selectByRelativeIndex(name, offset, region) {
      region = region || selectedRegion;
      if (region == null) {
        return null; // no selection
      }
      
      region = region.relatedRegion || region;

      var regions = self.excludedRegions();
      var idx = regions.indexOf(region);
      if (idx == -1) {
        console.log(name + ": Specified region not found, selection not updated");
        return selectedRegion;
      }

      idx = (idx + offset) % regions.length;
      if (idx < 0) {
        idx += regions.length;
      }
      console.log(name + ": Selecting region at idx=", idx, " (regions.length=", regions.length, ")");
      
      return self.selectRegion(regions[idx]);
    }
    
    self.selectPreviousRegion = function(region) {
      return selectByRelativeIndex("selectPreviousRegion", -1, region);
    };

    self.selectNextRegion = function(region) {
      return selectByRelativeIndex("selectPreviousRegion", 1, region);
    };

    // Highlights the region the mouse is over and updates the mouse cursor when in select mode
    function handleSelectMouseHover(e) {
      var pt = eventPositionToCanvasPt(e);
      var region = regionUnderPoint(pt);

      if (handleSelectMouseHover.lastRegion != region) {
        handleSelectMouseHover.lastRegion = region;

        self.selectRegion(region);

        var cursor = (region ? "pointer" : "default");
        //console.log("handleSelectMouseHover: set cursor=", cursor);
        $("#gcode_canvas").css({"cursor": cursor});
      }
    }

    // Selects the region under the mouse cursor when the user starts to drag the canvas
    function captureDragStartEventSelect(pt) {
      //console.log("captureDragStartEventSelect: pt=", pt);

      var region = self.selectRegionUnderPoint(pt);
      //console.log("captureDragStartEventSelect: selectRegionUnderPoint=", region);
      if (region != null) {
        $("#gcode_canvas").off("mousemove", handleSelectMouseHover);
        beginEditMode(region, "adjust");
        return false;
      }
    }

    var zHeightSubscription;
    function registerZHeightSubscription(callback) {
      if (zHeightSubscription) {
        unregisterZHeightSubscription();
      }
      
      zHeightSubscription = self.currentLayer.subscribe(function(value) {
        callback(value);
        console.log("zHeightSubscription: new layer=", value);
        $editRegionOverlay.tooltip('enable');
        $editRegionOverlay.tooltip('show');
      });
    }

    function unregisterZHeightSubscription() {
      if (zHeightSubscription) {
        zHeightSubscription.dispose();
      }
    }

    // Creates a new region at the specified point and starts capturing mouse events
    // when the user starts to drag the canvas
    function captureDragStartEventCreate(pt) {
      // Create a new region locally and prevent the default action
      if (selectedRegionType == "RectangularRegion") {
        self.selectRegion(new RectangularRegion(pt.x, pt.y, pt.x, pt.y, self.currentLayer()));
      } else if (selectedRegionType == "CircularRegion") {
        self.selectRegion(new CircularRegion(pt.x, pt.y, 0, self.currentLayer()));
      } else {
        throw new ArgumentError("Unsupported selectedRegionType: "+ selectedRegionType);
      }
      
      registerZHeightSubscription(function(value) {
          selectedRegion.minLayer = new Layer(value);
      });

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

        beginEditMode(selectedRegion, "adjust");
      }

      $gcodeCanvas.on("mousemove", mouseMoveHandler);
      $gcodeCanvas.on("mouseup", mouseUpHandler);

      beginEditMode(selectedRegion, "size");

      return false;
    }
    
    // Handles drag start events when resizing a region
    function captureDragStartEventSize(startPt) {
      console.log("captureDragStartEventSize: pt=", startPt);
      var near = selectedRegion.pointNearRegion(startPt, BASE_BORDER_RANGE / viewportScale);
      
      var isFullEditingEnabled = (editMode == "adjust");

      updateCursor(selectedRegion, startPt, isFullEditingEnabled);

      if (!near || (!isFullEditingEnabled && (near == INSIDE)))
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
          var relatedRegion = selectedRegion.relatedRegion || selectedRegion;

          if (selectedRegion instanceof RectangularRegion) {
            // Compute new edge position
            var x1 = relatedRegion.x1;
            var x2 = relatedRegion.x2;
            var y1 = relatedRegion.y1;
            var y2 = relatedRegion.y2;

            if (near & LEFT) {
              selectedRegion.x1 = (isFullEditingEnabled || pt.x <= x1 ? pt.x : x1);
            } else if (near & RIGHT) {
              selectedRegion.x2 = (isFullEditingEnabled || pt.x >= x2 ? pt.x : x2);
            }

            if (near & TOP) {
              selectedRegion.y1 = (isFullEditingEnabled || pt.y <= y1 ? pt.y : y1);
            } else if (near & BOTTOM) {
              selectedRegion.y2 = (isFullEditingEnabled || pt.y >= y2 ? pt.y : y2);
            }
          } else if (selectedRegion instanceof CircularRegion) {
            // Compute new size
            var r = Math.hypot(pt.x - selectedRegion.cx, pt.y - selectedRegion.cy);
            if (!isFullEditingEnabled)
              r = Math.max(r, relatedRegion.r);

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
    
    var _editPreviousLayerData;
    var _editLastLayerSelected;
    var _editOriginalFormatter;

    function _editOnChangeLayer(event) {
      var v = event.value;
      var v0Diff = (v[0] != _editPreviousLayerData[0]);
      var v1Diff = (v[1] != _editPreviousLayerData[1]);
      if (!(v0Diff || v1Diff)) {
        return;
      }
      _editPreviousLayerData[0] = v[0];
      _editPreviousLayerData[1] = v[1];

      var value = self.gcodeViewModel.maxLayer - (v0Diff ? v[0] : v[1]);

      console.log("changeLayer: original value=", v, " (", v0Diff, ",", v1Diff, ") forwarded value=", value, " maxLayer=", self.gcodeViewModel.maxLayer);

      if (v1Diff) {
        registerZHeightSubscription(function(value) {
            selectedRegion.minLayer = new Layer(value);
        });
      } else {
        registerZHeightSubscription(function(value) {
            selectedRegion.maxLayer = new Layer(value);
        });
      }

      _editLastLayerSelected = value;
      event.value = value
      self.gcodeViewModel.changeLayer(event);
    };
    
    function _editOverrideFormatter(value) {
      return _editOriginalFormatter.call(this, self.gcodeViewModel.maxLayer - value);
    }

    function hijackGcodeLayerSlider() {
      // Update the layer slider to show the current min and max layer for the selection
      var maxLayer = self.gcodeViewModel.maxLayer;
      var minLayerSel = selectedRegion.minLayer.number;
      var maxLayerSel = selectedRegion.maxLayer ? selectedRegion.maxLayer.number : maxLayer;
      _editOriginalOnChangeLayer = self.gcodeViewModel.changeLayer;
      _editPreviousLayerData = [maxLayer - maxLayerSel, -1];
      _editLastLayerSelected = minLayerSel;

      var slider = self.gcodeViewModel.layerSlider.data('slider');
      var value = [maxLayer - maxLayerSel, maxLayer - minLayerSel];
      _editOriginalFormatter = slider.formatter;
      slider.formatter = _editOverrideFormatter;
      slider.range = true;
      slider.reversed = false;
      slider.handle2.removeClass('hide');
      self.gcodeViewModel.layerSlider
        .off('slide', self.gcodeViewModel.changeLayer)
        .on('slide', _editOnChangeLayer)
        .slider("setValue", value);
        
      slider.element
				.trigger({
					'type': 'slide',
					'value': value
				})
				.data('value', value)
				.prop('value', value);
    }

    function restoreGcodeLayerSlider() {
      var slider = self.gcodeViewModel.layerSlider.data('slider');
      slider.formatter = _editOriginalFormatter;
      slider.range = false;
      slider.reversed = true;
      slider.handle2.addClass('hide');
      self.gcodeViewModel.layerSlider
        .off('slide', _editOnChangeLayer)
        .on('slide', self.gcodeViewModel.changeLayer)
        .slider("setValue", _editLastLayerSelected);

      slider.element
				.trigger({
					'type': 'slide',
					'value': _editLastLayerSelected
				})
				.data('value', _editLastLayerSelected)
				.prop('value', _editLastLayerSelected);
    }
    
    function endEditMode() {
      if (beginEditMode.lastSelector) {
        $(beginEditMode.lastSelector).hide();
        $("#gcode_exclude_controls .main").show();
        delete beginEditMode.lastSelector;
        self.selectRegion(null);
        editMode = null;

        // Remove hook for drag start event
        GCODE.renderer.setOption({
          "onDragStart" : null
        });
       
        // Remove handler for mouse move event
        var $gcodeCanvas = $("#gcode_canvas");
        $gcodeCanvas.off("mousemove", handleSelectMouseHover);
        $gcodeCanvas.off("mousemove", handleAdjustMouseHover);

        unregisterZHeightSubscription();
        restoreGcodeLayerSlider();
        
        renderExcludeRegionsOverlay(false);
      }
    }

    function beginEditMode(regionOrType, messageType) {
      editMode = messageType;
      if ((editMode == "adjust") && self.isEditingLimited()) {
        editMode = "adjust-limited";
      }

      if (regionOrType.type) {
        self.selectRegion(regionOrType);
      } else {
        self.selectRegion(null);
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
        case "new":
          onDragStart = captureDragStartEventCreate;
          break;
        case "size":
          break;
        case "select":
          onDragStart = captureDragStartEventSelect;
          renderExcludeRegionsOverlay(true);
          $gcodeCanvas.on("mousemove", handleSelectMouseHover);
          if (!self.isEditingLimited()) {
            $deleteButton.show();
          }
          break;
        case "adjust":
        case "adjust-limited":
          onDragStart = captureDragStartEventSize;
          renderExcludeRegionsOverlay(true);
          $gcodeCanvas.on("mousemove", handleAdjustMouseHover);
          $acceptButton.removeClass("disabled");

          // Enable the delete button if the selected region has been committed to the server and
          // editing is not limited
          if (selectedRegion != null && selectedRegion.id != null && !self.isEditingLimited()) {
            $deleteButton.show();
            $deleteButton.removeClass("disabled");
          }
          
          unregisterZHeightSubscription();
          hijackGcodeLayerSlider();

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
                '<span class="text new">'+
                  '<i class="fa fa-crosshairs"></i>'+ gettext("Click to set first corner")+
                '</span>'+
                '<span class="text size">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag to adjust size")+
                '</span>'+
                '<span class="text adjust">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag interior to reposition or border to resize")+
                '</span>'+
                '<span class="text adjust-limited">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag border to resize")+
                '</span>'+
              '</span>'+
              '<span class="region CircularRegion">'+
                '<div class="label"><i class="fa fa-times-circle-o"></i>'+ gettext("Circle") +'</div>'+
                '<span class="text new">'+
                  '<i class="fa fa-dot-circle-o"></i>'+ gettext("Click to set center point")+
                '</span>'+
                '<span class="text size">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag to adjust size")+
                '</span>'+
                '<span class="text adjust">'+
                  '<i class="fa fa-arrows"></i>'+ gettext("Drag interior to reposition or border to resize")+
                '</span>'+
                '<span class="text adjust-limited">'+
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
              beginEditMode("RectangularRegion", "new");
            } else if ($button.hasClass("excludeCircle")) {
              beginEditMode("CircularRegion", "new");
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

    self.addAtCommandAction = function() {
      var $command = $("#settings-excluderegion_newAtCommand");
      var command = $command.val().trim();

      var $parameterPattern = $("#settings-excluderegion_newAtCommandParameterPattern");
      var parameterPattern = $parameterPattern.val().trim();

      var $action = $("#settings-excluderegion_newAtCommandAction");
      var action = $action.val();

      var $desc = $("#settings-excluderegion_newAtCommandDescription");
      var desc = $desc.val();

      self.settings.atCommandActions.push({
        "command": ko.observable(command),
        "parameterPattern": ko.observable(parameterPattern),
        "action": ko.observable(action),
        "description": ko.observable(desc)
      });

      $command.val('');
      $parameterPattern.val('');
      $action.val('enable_exclusion');
      $desc.val('');
    }
    
    self.removeAtCommandAction = function(row) {
      self.settings.atCommandActions.remove(row);
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
      var p1 = transformViewToDrawing(0, 0);
      var p2 = transformViewToDrawing(ctx.canvas.width, ctx.canvas.height);
      ctx.clearRect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y);
    }

    function renderEditRegionOverlay_callback() {
      var ctx = editRegionOverlayContext;
      ctx.save();

      clearContext(ctx);

      if (selectedRegion != null) {
        ctx.globalAlpha = RENDER_REGION_ALPHA;
        ctx.fillStyle = RENDER_FILL_SELECTED;
        ctx.lineWidth = RENDER_BORDER_WIDTH / viewportScale;
        ctx.strokeStyle = RENDER_STROKE_SELECTED;

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

      ctx.globalAlpha = RENDER_REGION_ALPHA;
      ctx.lineWidth = RENDER_BORDER_WIDTH / viewportScale;
      ctx.strokeStyle = RENDER_STROKE_NORMAL; //GCODE.renderer.getOptions().colorGrid;

      var regions = self.excludedRegions();
      var selRegion;

      for (var i = regions.length - 1; i >= 0; --i) {
        var region = regions[i];
        if (selectedRegion && (region.id == selectedRegion.id)) {
          // Save to draw selected region last
          selRegion = region;
        } else {
          ctx.fillStyle = region.inHeightRange(self.currentLayer().height) ? RENDER_FILL_NORMAL : ctx.strokeStyle;
          ctx.beginPath();
          region.renderPath(ctx);
          ctx.fill();
        }
      }

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

    var _xformSvg = document.createElementNS("http://www.w3.org/2000/svg",'svg');
    var _xformPt = _xformSvg.createSVGPoint();
    overlayXform = _xformSvg.createSVGMatrix();

    function transformViewToDrawing(x,y) {
        _xformPt.x=x; _xformPt.y=y;
        return _xformPt.matrixTransform(overlayXform.inverse());
    }

    function transformDrawingToView(x,y) {
        _xformPt.x=x; _xformPt.y=y;
        return _xformPt.matrixTransform(overlayXform);
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

      previousOnViewportChange = GCODE.renderer.getOptions().onViewportChange;
      
      // Hook into the GCODE viewer to render the exclude regions
      GCODE.renderer.setOption({
        onViewportChange: function(xform) {
          overlayXform = xform;
          excludeRegionsOverlayContext.setTransform(xform.a, xform.b, xform.c, xform.d, xform.e, xform.f);
          editRegionOverlayContext.setTransform(xform.a, xform.b, xform.c, xform.d, xform.e, xform.f);
          updateViewportScale();
          renderExcludeRegionsOverlay();
          renderEditRegionOverlay();
          // Invoke any previously registered viewport change handler to ensure we don't interfere
          // with other plugins which may also be listening.
          if (previousOnViewportChange)
            previousOnViewportChange(xform);
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
      
      previousOnLayerSelected = self.gcodeViewModel._onLayerSelected;
      self.gcodeViewModel._onLayerSelected = function(layer) {
        previousOnLayerSelected(layer);
        self.currentLayer(layer ? new Layer(layer.number, layer.height) : null);
        renderExcludeRegionsOverlay();
      };

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