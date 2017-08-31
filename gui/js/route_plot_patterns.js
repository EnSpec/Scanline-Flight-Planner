
//returns a 'snake' pattern over the specified rectangular area
// eg
// *-* *-* *-*
// | | | | | |
// | | | | | |
// * *-* *-* *
var grid_pattern = function(start,width,height,step){
    coords = [];
    var ys=_.range(start.y-height/2,start.y+height/2+step,step);
    _.each(ys,function(y,idx){
       var top_coord = {x:start.x+width/2,y:y}; 
       var bot_coord = {x:start.x-width/2,y:y};
       if(idx%2){
           coords.push(top_coord);
           coords.push(bot_coord);
       }else{
           coords.push(bot_coord);
           coords.push(top_coord);
       };
    });
    coords.push({x:0,y:0});
    return coords;
};
