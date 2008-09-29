# Copyright (c) 2005-2008, California Institute of Technology
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author: Andrew D. Straw

from __future__ import division
import os, hashlib
import Image
import pylab
import numpy

R2D=180/numpy.pi
D2R=1/R2D

def check_eye_map_gif(fname):
    # Ensure that the eye_map.gif file is what is expected.
    if not os.path.exists(fname):
        raise RuntimeError('The file "%s" was not found. Download from '
        'http://code.astraw.com/projects/drosophila_eye_map/download/eye_map.gif'%(
            fname,))
    m = hashlib.md5()
    m.update( open(fname,mode='rb').read() )
    actual_md5 = m.hexdigest()
    expected_md5 = '4ba242820fd02c398fcde5cdec38e62d'
    if not expected_md5==actual_md5:
        raise RuntimeError('The file "%s" had an unexpected md5sum. Download from '
        'http://code.astraw.com/projects/drosophila_eye_map/download/eye_map.gif'%(
            fname,))

fname = 'eye_map.gif'
check_eye_map_gif(fname)
im = Image.open(fname)
aspect_ratio = im.size[0]/im.size[1]
# center of image coordinates:


if 0:
    center=(.7152,.5022)
    im_scale=(2/.427,2/.4232)
    im_extent=(im_scale[0]*(0-center[0]),
               im_scale[0]*(aspect_ratio-center[0]),
               im_scale[1]*(0-center[1]),
               im_scale[1]*(1-center[1]))
else:
    # flip x axis so positive is right on figure and anterior
    center=(.7247,.5023)
    im_scale=(2/.4268,2/.4248)
    im_extent=(im_scale[0]*(aspect_ratio-center[0]),
               im_scale[0]*(0-center[0]),
               im_scale[1]*(0-center[1]),
               im_scale[1]*(1-center[1]))

def get_rot_mat(theta,x,y,z):
    # see http://en.wikipedia.org/wiki/Rotation_matrix
    cos = numpy.cos(theta)
    sin = numpy.sin(theta)
    M = numpy.array([[cos+(1-cos)*x**2, (1-cos)*x*y+sin*z, (1-cos)*x*z-sin*y],
                     [(1-cos)*y*x-sin*z, cos+(1-cos)*y**2, (1-cos)*y*z+sin*x],
                     [(1-cos)*z*x+sin*y, (1-cos)*z*y-sin*x, cos+(1-cos)*z**2]])
    return M

rot90 = get_rot_mat(-numpy.pi/2,1,0,0)

def xform_long_lat_2_stereographic(long,lat,R=1.0):
    theta_P = long
    rho_P = 2*R*numpy.tan((numpy.pi/2-lat)/2.0)

    x=rho_P*numpy.cos(theta_P)
    y=rho_P*numpy.sin(theta_P)

    return x,y

def xform_stereographic_2_long_lat(x,y,R=1.0):
    x=numpy.asarray(x)
    y=numpy.asarray(y)
    R=numpy.asarray(R)
    # convert to 2D polar
    rho = numpy.sqrt(x**2+y**2)
    theta = numpy.arctan2(y,x)

    # convert to spherical
    colat = 2*numpy.arctan(rho/(2*R))
    lat = numpy.pi/2-colat

    long = theta

    return long, lat, R

class LongLatRotator:
    def __init__(self,rotmatrix):
        self.rotmatrix = rotmatrix
    def __call__(self,long,lat,R=1.0):
        sin,cos,pi = numpy.sin, numpy.cos, numpy.pi

        M = self.rotmatrix

        colat = pi/2 - lat

        # first, transform to 3D cartesian
        x3 = R*sin(colat)*cos(long)
        y3 = R*sin(colat)*sin(long)
        z3 = R*cos(colat)

        # next, transform to new 3D cartesian
        xn = M[0,0]*x3 + M[0,1]*y3 + M[0,2]*z3
        yn = M[1,0]*x3 + M[1,1]*y3 + M[1,2]*z3
        zn = M[2,0]*x3 + M[2,1]*y3 + M[2,2]*z3

        # finally, transform back to long, lat
        rho = numpy.sqrt( xn**2 + yn**2 + zn**2 )
        longn = numpy.arctan2(yn,xn)
        colatn = numpy.arctan2( numpy.sqrt(xn**2 + yn**2), zn )

        latn = pi/2-colatn
        return longn,latn,rho

Mforward = get_rot_mat(-numpy.pi/2,1,0,0)
scale = numpy.eye(3)
scale[2,2]=-1
Mforward = numpy.dot(Mforward,scale)
xform_my_long_lat_2_heisenberg = LongLatRotator(Mforward)
Mreverse = numpy.linalg.inv(Mforward)
xform_heisenberg_long_lat_2_my = LongLatRotator(Mreverse)

def xform_my_long_lat_2_heisenberg_old(long,lat,R=1.0):
    sin,cos,pi = numpy.sin, numpy.cos, numpy.pi

    colat = pi/2 - lat

    # first, transform to 3D cartesian
    x3 = R*sin(colat)*cos(long)
    y3 = R*sin(colat)*sin(long)
    z3 = R*cos(colat)

    # next, transform to new 3D cartesian
    xn = rot90[0,0]*x3 + rot90[0,1]*y3 + rot90[0,2]*z3
    yn = rot90[1,0]*x3 + rot90[1,1]*y3 + rot90[1,2]*z3
    zn = rot90[2,0]*x3 + rot90[2,1]*y3 + rot90[2,2]*z3

    # finally, transform back to long, lat
    rho = numpy.sqrt( xn**2 + yn**2 + zn**2 )
    longn = numpy.arctan2(yn,xn)
    colatn = numpy.arctan2( numpy.sqrt(xn**2 + yn**2), zn )

    latn = pi/2-colatn
    return longn,latn,rho

##    # pass through old
##    return xform_long_lat_stereographic(longn,latn,rho)

if 0:
    long,lat = invert( 2.129, .9204 )
    print long*R2D, lat*R2D
    print xform_long_lat(long,lat)
    print

fig=pylab.figure()
ax1=fig.add_axes([.1,.1,.8,.8],label='image')
if 1:
    ax1.imshow(im,origin='lower',
               extent=im_extent,
               aspect='equal')
#ax1.plot([0.0],[0.0],'rx')

if 1:

    lat=numpy.linspace(-numpy.pi/2,numpy.pi/2,30)

    for this_long in numpy.array([0.0,40.0,90.0])*D2R:
    #for this_long in numpy.linspace(0,numpy.pi,19):
        long=this_long*numpy.ones_like(lat)
        if 1:
            hlong,hlat,hrho = xform_my_long_lat_2_heisenberg(long,lat)
            x,y = xform_long_lat_2_stereographic(hlong,hlat,hrho)
            ax1.plot(x,y)
        if 0:
            #x,y=xform_long_lat(this_long,8/9*(-numpy.pi/2))
            x,y=xform_long_lat(this_long,0)#-numpy.pi/2)
            print this_long*R2D,':',x,y
            print
            ax1.plot([x],[y],'rx')

    x= [2.1679711947690445, 2.1888012950502311,
        2.2073169397446186, 2.1888012950502311, 2.2258325844390061,
        2.2096313953314173, 2.2674927850013784]

    y= [0.74328116407792189, 0.57664036182843226,
        0.43777302662052431, 0.28039004671822865, 0.13457934474992517,
        -0.025118090739169041, -0.16861433712067397]

    x.extend([1.9680080767875927, 1.9711850396787738,
              1.9902468170258598, 2.0093085943729458, 2.0696708893053852,
              2.044255186175937, 2.0855557037612904, 2.0633169635230231,
              2.044255186175937, 2.1300331842378242, 1.9870698541346787,
              2.0855557037612904, 2.0601400006318418, 2.1872185162790823,
              2.2698195514497885, 1.9203536334198776, 1.9235305963110585,
              2.1046174811083764, 1.767859414643189])

    y.extend([1.1219096504902504, 0.94399972858411396,
              0.78197462113388228, 0.61994951368365103, 0.4642783320157815,
              0.29907626167436896, 0.15611293157122352, 0.000441749903353994,
              -0.12345980285270541, -0.26642313295585085, -0.34584720523537604,
              -0.46974875799143545, -0.61271208809458089, -0.48881053533852148,
              -0.63495082833284788, -0.71119793772119222, -0.85098430493315658,
              -0.91452356275677682, -0.80650682445662247])
    print len(x)
    x.extend([2.129,1.428])
    y.extend([.9204,-.3218])

    x+=[2.1845100345831998, 1.9646833326904964, 1.787866202907235, 1.9837986980724707, 1.9861881187452173, 1.8045921476164624, 1.6445009625424285, 1.6014913904329864, 1.4652944120864202, 1.4844097774683944, 1.6612269072516559, 1.3267080130671072, 1.2860878616304121, 1.1092707318471506, 0.88227576793620699]
    y+= [-1.0741117074118767, -0.99048198386573949, -0.94986183242904443, -1.1672991136490007, -1.3321691400685283, -1.2509288371951381, -1.186414479030975, -1.3656210294869833, -1.4588084357241073, -1.6881928203077978, -1.568721786670459, -1.7933273299086561, -1.580668890034193, -1.6881928203077978, -1.824389798654364]

    x+= [1.8234916024875814, 1.8035062200427303, 1.0859841827900749, 0.84617215031367277, 0.6241839851159221, 0.68737769637659563, 0.50589832044850747, 0.32117824137884621, 0.1996518735698587, 0.38113124949794686, 0.56099027385524858, 0.72302543093389859, 0.94339324456086282, 1.1054284016395131, 1.3063519964170394, 1.4667668019249029]
    y+= [-1.4488503096126486, -1.1130958845391525, -1.9476561311242164, -2.0432568738006198, -2.0983488272073609, -1.923350857562419, -1.981683514110733, -2.0432568738006198, -1.9298322638455649, -1.8617774978725319, -1.7985837866118581, -1.7062237470770276, -1.6057619496882645, -1.5053001522995015, -1.3870144876320869, -1.2914137449556833]

    x+= [1.8214613014564094, 1.7852420276363388, 1.7466081355615968, 1.5679263847159155, 1.466512418019718, 1.3288791775034499, 1.2467821568446233, 1.0632711694895993, 0.90390636468128882, 1.0053203313774863, 1.1646851361857968, 1.2081482647698814, 1.3264645592487785, 1.427878525944976, 1.6089748950453289, 1.6717549696667846, 1.4882439823117604, 1.5244632561318308, 1.6838280609401413, 1.8238759197110808, 1.6814134426854699, 1.8480221022577945, 1.7248765712695546, 1.8673390482951655, 1.7441935173069254, 1.8938998490965506, 1.7683396998536391, 1.930119122916621, 1.7659250815989678]
    y+= [0.96675578795928752, 1.1454375388049689, 1.3217046713959788, 1.3265339079053216, 1.5269472230430452, 1.5221179865337024, 1.6790681730873414, 1.7225313016714261, 1.7394336294541257, 1.5414349325710734, 1.5462641690804162, 1.3458508539426925, 1.3241192896506502, 1.1623398665876685, 1.1647544848423399, 0.98365811574198714, 1.0029750617793578, 0.87017105777243275, 0.82187869267900526, 0.80256174664163427, 0.6600992696160235, 0.6407823235786525, 0.52246602909975537, 0.47900290051567074, 0.3800035520741446, 0.32205271396203172, 0.22063874726583416, 0.19649256471912047, 0.085420125004237457]

    x+= [1.903291360713895, 1.8029996014743306, 1.9223945529500026, 1.8029996014743306, 1.924782451979516, 1.8053875005038442, 1.8650849762416801, 1.9009034616843818, 1.7074836402937932, 1.6645014577625514, 1.6071918810542289, 1.6239071742608229, 1.4639179392834225, 1.4830211315195301]
    y+= [0.041165782885357771, -0.059125976354206689, -0.080617067619827676, -0.1785209278298785, -0.22150311036112047, -0.30269167736457736, -0.42925032592878942, -0.57013636867008222, -0.52476628710932693, -0.4029834366041416, -0.74206509879504978, -1.0310008813661757, -0.96413970853979947, -1.1265168425467131]

    x+= [1.6084967354554651, 1.2884635615137443, 1.1460210505685853, 1.162670175224513, 1.3273115190442422, 1.3088124916487671, 1.2903134642532919, 1.4679041272498536, 1.429056169719356, 1.543750139571302, 1.3828086012306677, 1.5474499450503971, 1.4050074341052381, 1.5289509176549219, 1.4050074341052381, 1.5659489724458724, 1.6602940121627958, 1.6861926505164611, 1.5252511121758268, 1.3846585039702153, 1.2884635615137443, 1.1663699807036081, 1.2903134642532919, 1.3106623943883147, 1.1645200779640605, 1.1663699807036081, 1.2607150204205315, 1.2681146313787215, 1.1645200779640605, 1.1219723149544676, 1.1423212450894904, 1.0257773724979966, 1.1608202724849654, 1.0276272752375442, 0.9850795122279512, 0.80378904375229432, 0.68354536568170543, 0.84633680676188705, 0.88703466703193268, 0.90738359716695527, 0.92588262456243053, 1.0239274697584491, 1.0257773724979966, 0.92218281908333544, 0.94808145743700067, 1.0442763998934717, 1.0442763998934717, 0.9443816519579058, 1.0479762053725667, 1.0442763998934717, 1.1404713423499429, 1.0461263026330192, 0.92218281908333544, 0.80563894649184165, 0.82228807114776936, 0.81858826566867426, 0.72424322595175084, 0.82598787662686446, 0.72239332321220329, 0.80563894649184165, 0.7020443930771807, 0.82228807114776936, 0.70574419855627557, 0.80933875197093674, 0.76494108622179624, 0.66689624102577771, 0.62434847801618476, 0.70574419855627557, 0.56145178487156921, 0.54295275747609395, 0.44120810680098033, 0.48375586981057328, 0.5448026602156415, 0.56330168761111676, 0.58365061774613936, 0.60399954788116217, 0.60214964514161462, 0.62434847801618476, 0.60029974240206707, 0.70574419855627557, 0.60214964514161462, 0.72424322595175084, 0.52445373008061869, 0.40236014927048247, 0.50225489720604855, 0.50225489720604855, 0.39866034379138737, 0.40051024653093492, 0.4967051889874059, 0.38016131639591211, 0.49855509172695345, 0.38201121913545966, 0.35981238626088952, 0.46525684241509802, 0.31911452599084411, 0.44490791228007542, 0.3024654013349164, 0.38201121913545966, 0.34131335886541425, 0.28211647119989358, 0.19517104244116013, 0.23956870819030085, 0.18222172326432773, 0.21921977805527781, 0.25806773558577589, 0.26176754106487099, 0.17852191778523263, 0.18037182052478018, 0.27656676298125116, 0.2987655958558213, 0.19887084792025522, 0.2950657903767262, 0.19517104244116013, 0.29691569311627375, 0.4422853273687295]
    y+= [-0.88486196055780786, -1.2067450372390762, -1.3066397851746423, -1.1253493166989854, -1.0513532071170846, -0.90521089069283056, -0.77016799070586162, -0.82751497563183474, -0.68692236742622326, -0.6036767441465849, -0.54078005100196935, -0.46493403868052097, -0.42423617841047556, -0.3446903606099323, -0.19484823870658308, -0.24294570993481868, -0.26144473733029372, -0.14120105925970505, -0.11530242090603982, -0.078304366115089508, -0.13750125378060996, -0.21889697432070077, -0.26329464006984127, -0.38168841540088261, -0.3409905551308372, -0.46123423320142587, -0.50748180169011392, -0.62587557702115515, -0.58517771675110963, -0.70727129756124596, -0.82566507289228719, -0.88671186329735541, -0.96440777835835123, -1.0458034988984419, -1.2252440646345515, -1.3084896879141898, -1.227093967374099, -1.1438483440944607, -0.96810758383744622, -0.82751497563183474, -0.70542139482169852, -0.74611925509174393, -0.64622450715617785, -0.58517771675110963, -0.48343306607599623, -0.52598082908558919, -0.4057371510150003, -0.36133948526585979, -0.29844279212124425, -0.18189891952975046, -0.10050319898965965, -0.061655241459161791, -0.14120105925970505, -0.080154268854636834, -0.19669814144613063, -0.32064162499581439, -0.36133948526585979, -0.42608608115002311, -0.48343306607599623, -0.54447985648106423, -0.58702761949065718, -0.64622450715617785, -0.70912120030079351, -0.76646818522676663, -0.88486196055780786, -0.83121478111092983, -0.96440777835835123, -1.0476534016379895, -1.1253493166989854, -1.3121894933932849, -1.2030452317599811, -1.0476534016379895, -0.88486196055780786, -0.76831808796631418, -0.6443746044166303, -0.54447985648106423, -0.42238627567092801, -0.31879172225626684, -0.20224784966477327, -0.15970008665518032, -0.11900222638513491, -0.043156214063686527, -0.061655241459161791, -0.12085212912468224, -0.15970008665518032, -0.26329464006984127, -0.21889697432070077, -0.32249152773536194, -0.37983851266133506, -0.42423617841047556, -0.48528296881554356, -0.52228102360649409, -0.64622450715617785, -0.70727129756124596, -0.74611925509174393, -0.82751497563183474, -0.88671186329735541, -0.96625768109789867, -1.1253493166989854, -1.2659419249045969, -1.188246009843601, -1.0236046660238718, -0.82566507289228719, -0.68322256194712827, -0.56852859209518214, -0.46123423320142587, -0.42793598388957066, -0.32064162499581439, -0.36503929074495489, -0.26329464006984127, -0.22259677979979586, -0.18004901679020291, -0.13565135104106241, -0.083854074333731932, 1.1211245929330724]

    x+= [1.6464115756965303, 1.5086054637171831, 1.2658042188011902, 1.1454972956446172, 0.90050865212577746, 0.8217623024232934, 0.60520984074146189, 0.42146835810233219, 0.20054109921480734, 0.10210816208670215, 0.10210816208670215, 0.084608973263927911, 0.060547588632613003, 0.058360190029766557, 0.16335532296641198]
    y+= [-0.021416452717133994, 0.024518917942648377, -0.019229054114287214, 0.024518917942648377, -0.019229054114287214, 0.024518917942648377, 0.00045753331133380204, -0.021416452717133994, -0.045477837348448569, -0.09578800521392461, -0.17890915212210234, -0.27734208925020742, -0.38452462078969979, -0.46108357188933713, -0.50701894254911961]

    x+= [0.039971607669287756, -0.015885560048661151, 0.09582877538723622, 0.30207062542273899, 0.17746617435962264, 0.0013012607876308202, 0.082938659760017241, 0.22043322645035257, 0.32355415146810396, 0.44386189732214731, 0.61143340047599359, 0.48253224420380425, 0.37941131918605286, 0.66299386298486906, 0.80908184009335038, 0.95946652241090447]
    y+= [-1.9571228391022935, -1.884078850548053, -1.7938480411575206, -1.7551776942758637, -1.6348699484218203, -1.6735402953034773, -1.514562202567777, -1.4587050348498283, -1.5575292546585069, -1.6778370005125502, -1.6047930119583094, -1.5016720869405582, -1.3770676358774419, -1.4071445723409526, -1.5059687921496312, -1.4028478671318796]

    x+= [0.32292391299017353, 0.40222127906105909, 0.50220491454174132, 0.48496635670024446, 0.59874083845412396, 0.70561989707140471, 0.70561989707140471, 0.80215582098378735, 0.9090348796010681, 1.0055708035134505, 1.026257072923247, 1.1262407084039288, 1.2296720554529101, 1.2469106132944072, 1.3710282297531848, 1.3503419603433886, 1.4882504230753637, 1.6261588858073388, 1.6089203279658419, 1.4675641536655675, 1.4641164420972681, 1.6089203279658419, 1.5916817701243451, 1.3331034025018915, 1.3296556909335921, 1.2296720554529101, 1.1055544389941325, 1.1021067274258332, 1.0055708035134505, 0.90558716803276851, 0.90558716803276851, 0.80560353255208672, 0.76767870530079341, 0.68493362766160826, 0.58839770374922584, 0.56426372277113002, 0.46083237572214886, 0.37808729808296349, 0.364296451809766, 0.2781036626022817, 0.24017883535098861, 0.16432918084840198, 0.06089783379942082, 0.047106987526223332, -0.059772071091057644, -0.097696898342350735, -0.17699426441323629, -0.27353018832561915, -0.29766416930371475, -0.32179815028181036, -0.21147138009623001, -0.23905307264262499, -0.11838316775214697, -0.0011609744299678759, 0.10571808418731266, 0.12295664202880952, 0.22294027750949175, 0.34016247083167039, 0.3022376435803773, 0.443593817880652, 0.46083237572214886, 0.55047287649793253, 0.64356108884201579, 0.64700880041031517, 0.75044014745929655, 0.86421462921317604, 0.84697607137167918, 0.96419826469385805, 1.0814204580160369, 1.0676296117428394, 1.2089857860431139, 1.2089857860431139, 1.3331034025018915, 1.2882831521139997, 1.4124007685727773, 1.4641164420972681, 1.5675477891462495]
    y+= [0.020459952527941416, 0.082518760757330334, 0.041146221937737648, 0.13768214585012029, 0.10320503016712657, 0.061832491347534102, 0.17560697310141338, 0.14457756898671903, 0.10320503016712657, 0.065280202915833474, 0.17905468466971275, 0.14112985741841966, 0.22042722348930543, 0.10665274173542594, 0.05838477977923473, 0.17905468466971275, 0.14112985741841966, 0.099757318598827194, 0.26869518544549664, 0.2859337432869935, 0.44797618699706443, 0.40315593660917237, 0.56864609188754267, 0.32730628210658619, 0.46521474483856129, 0.36178339778957991, 0.2617997623088979, 0.40315593660917237, 0.30317230112849036, 0.34799255151638242, 0.22732264662590418, 0.23766578133080229, 0.38591737876767551, 0.30317230112849036, 0.22042722348930543, 0.34454483994808305, 0.26524747387719727, 0.17905468466971275, 0.30317230112849036, 0.21697951192100606, 0.34454483994808305, 0.25835205074059853, 0.1997409540795092, 0.30317230112849036, 0.23766578133080229, 0.34454483994808305, 0.2859337432869935, 0.23766578133080229, 0.31696314740168807, 0.4238422060189686, 0.399708225040873, 0.49969186052155501, 0.46521474483856129, 0.4238422060189686, 0.50313957208985438, 0.38591737876767551, 0.46176703327026192, 0.42039449445066923, 0.5376166877728481, 0.50313957208985438, 0.39626051347257363, 0.44452847542876506, 0.42039449445066923, 0.5376166877728481, 0.50658728365815375, 0.46521474483856129, 0.62036176541203325, 0.5651983803192433, 0.54106439934114747, 0.68931599677802069, 0.50313957208985438, 0.66518201579992509, 0.62036176541203325, 0.74792709343911001, 0.72724082402931378, 0.58243693816074016, 0.68242057364142195]
    x+= [0.062415030471587585, 0.1375557938350469, 0.18317697159143287, 0.26100133364644451, 0.40054846560715451, 0.52667760411010422, 0.47837282766216616, 0.60181836747356354, 0.72794750597651325, 0.68769352560323127, 0.80845546672307678, 0.92921740784292206, 0.8862798287780882, 0.97752218429086024, 1.1304873097093311, 1.0848661319529449, 1.2351476586798635, 1.3881127840983345, 1.3317572115757399, 1.2458820534460722, 1.1707412900826129, 1.1304873097093311, 0.98557298036551655, 1.0472957502712155, 0.96678778952465172, 0.92653380915136996, 0.84334224971325433, 0.72526390728496093, 0.76551788765824291, 0.62328715700598059, 0.56424798579183388, 0.48105642635371826, 0.41933365644801945, 0.33882569570145593, 0.28247012317886133, 0.22343095196471485, 0.078516622620900423, 0.024844648789857926, -0.020776528966528041, -0.074448502797570537, -0.13617127270326934, -0.21936283214138497, -0.082499298872226845, -0.23546442429069758, -0.17910885176810298, 0.00069226056588878038, 0.038262642247618439, 0.11877060299418218, 0.23953254411402747, 0.35761088654232065, 0.30125531401972627, 0.47837282766216616, 0.56424798579183388, 0.6420723478468453, 0.78698667719065973, 0.70647871644409621, 0.84602584840480644, 0.76820148634979502, 0.92385021045981786, 1.0660809411120802, 0.84870944709635854, 0.70647871644409621, 0.62328715700598059, 0.47837282766216616, 0.56424798579183388, 0.41933365644801945, 0.36029448523387275, 0.28247012317886133, 0.23953254411402747, 0.18049337289988077, 0.12145420168573429, 0.05704783308848338, -0.039561719807392981, -0.098600891021539461, -0.15764006223568616, -0.21936283214138497, -0.29450359550484428, -0.35890996410209519, -0.45283591830641923, -0.51455868821211803, -0.39379674709227253, -0.23814802298224969, -0.20057764130052025, -0.12006968055395628, -0.10128448971309156, -0.0046749368172154249, 0.059731431780035482, 0.15365738598435974, 0.20464576112384991, 0.31735690616903889]
    y+= [0.62000457570714573, 0.70319613514526136, 0.57975059533386375, 0.6629421547719796, 0.62000457570714573, 0.57975059533386375, 0.72466492467767818, 0.68172734561284432, 0.64147336523956255, 0.78370409589182488, 0.74345011551854312, 0.72466492467767818, 0.84542686579752369, 0.82127447757355454, 0.78638769458337698, 0.94203641869339982, 0.92861842523563931, 0.88568084617080545, 1.0466967676639325, 1.1862438996246427, 1.0654819585047974, 1.2077126891570598, 1.2238142813063724, 1.0869507480372145, 0.98497399775823391, 1.1245211297189441, 1.0064427872906507, 1.0466967676639325, 0.88836444486235755, 0.93130202392719141, 0.82127447757355454, 0.96350520822581687, 0.8615284579468363, 0.76760250374251227, 0.90714963570322249, 0.80248928673268982, 0.82395807626510664, 0.74345011551854312, 0.8642120566383884, 0.77833689850872068, 0.90178243832011806, 0.82395807626510664, 0.98229039906668181, 1.0252279781315157, 1.1218375310273918, 1.08158355065411, 0.94740361607650425, 1.0654819585047974, 1.0413295702808283, 1.0010755899075465, 1.1406227218682568, 1.2238142813063724, 1.0842671493456622, 1.1996618930824035, 1.1433063205598089, 1.3043222420529361, 1.261384662988102, 1.4224005844812291, 1.3848302027994996, 1.3633614132670826, 1.5834165059743566, 1.5995180981236692, 1.4841233543869279, 1.5216937360686578, 1.3445762224262179, 1.4036153936403644, 1.2587010642965499, 1.4411857753220942, 1.3016386433613838, 1.1835603009330906, 1.3204238342022487, 1.1835603009330906, 1.3150566368191445, 1.2023454917739556, 1.3177402355106966, 1.2184470839232682, 1.3579942158839784, 1.2560174656049978, 1.4170333870981249, 1.3150566368191445, 1.5592641177503872, 1.4760725583122716, 1.6370884798053986, 1.4733889596207195, 1.6156196902729818, 1.459970966162959, 1.6022016968152213, 1.4626545648545111, 1.5807329072828045, 1.5592641177503872]
    x+= [2.0830740377432635, 1.7599728320615931, 0.16142388357785142, -0.04269537685326652, 0.096624118361623434, 0.090144141840000636, 0.19058377792515424, 0.2845434374886846]
    y+= [-0.75236239305380215, -0.64690574953270141, 0.927773511093686, 0.54221490805712969, 0.10481649284759098, 0.007616845023248997, 0.075656598500288386, 0.11777644589083658]

    x+= [0.14106986135781341, 0.061961590971935099, 0.083936110523568086, 0.044381975330628709, 0.13667495744748681, 0.083936110523568086, 0.11909534180618087, 0.018012551868669124, 1.0024710277818247, 0.13971697358663016, 0.039271408532485896, 0.18107691213833665, 0.15547314065394691, 0.25591870570809117, 0.33863858281150416, 0.33863858281150416, 0.37802900047979593, 0.45877935669979442, 0.5198345040856468, 0.53952971291979268, 0.60058486030564506, 0.66360952857491207]
    y+= [-1.3476517081178987, -1.259753629911367, -1.1059319930499365, -0.88179189362328048, -0.93892564445752624, -0.75873458413413619, -0.62249256291401189, -0.58293842772107274, 0.449863991205675, 1.7590853035732141, 2.0111839766502819, 1.8969517654122356, 2.0170925393005259, 1.7334815320888244, 1.8555918268605291, 2.0151230184171114, 1.6980301561873616, 1.8358966180263832, 1.9757326007488194, 1.6606092594024844, 1.7984757212415059, 1.9737630798654047]
    x+= [0.76939498073518653, -0.084629318405484044, -0.17955509669898984, -0.29739399389092824, -0.19592161019787024, -0.31703381008958464, -0.43487270728152261, -0.33667362628824105, -0.47415233967883541, -0.53634509097458061, -0.62472426386853419, -0.71637673946226421, -0.8014826096564418, -1.0469803121396466, -1.1648192093315846, -0.87676857175129141, -0.9422346257468126, -0.8440355447535306, -0.75238306915980102, -0.69673692326360781, -0.57562472337189341, -0.65418398816651901, -0.49379215587749181, -0.42177949648241864, -0.35631344248689745, -0.28102748039204783, -0.31703381008958464, -0.3759532586855534, -0.45451252348017901, -0.53307178827480461, -0.57235142067211742, -0.65418398816651901, -0.75238306915980102, -0.83748893935397861, -0.89968169064972381, -0.97496765274457298, -1.0175205878416618, -1.0862599445369594, -1.1582726039320326, -1.076440036437631, -1.1157196688349438, -1.0207938905414378, -0.95532783654591658, -0.85385545285285858, -0.83421563665420218, -0.73601655566092061, -0.67709710706495141, -0.57562472337189341, -0.41195958838309021, -0.25811436149361544, -0.32030711278936064, -0.17955509669898984, -0.06171619950705165, -0.13700216160190104]
    y+= [1.7851554883788783, 1.781588337998965, 1.8994272351909034, 1.9157937486897838, 1.775041732599413, 1.781588337998965, 1.8175946676965018, 1.673569348906355, 1.6997557705045638, 1.6015566895112818, 1.4804444896195674, 1.6539295327076986, 1.555730451714417, 1.4738978842200154, 1.3331458681296446, 1.4378915545224786, 1.3200526573305402, 1.1596608250415135, 1.254586603335019, 1.352785684328301, 1.2218535763372582, 1.1400210088428571, 1.0974680737457683, 1.1793006412401694, 1.0614617440482315, 1.1465676142424091, 0.94034954415651717, 0.86179027936189156, 0.98617578195338196, 0.90106991175920437, 1.0221821116509187, 0.94034954415651717, 1.0418219278495751, 0.96326266305494956, 1.0811015602468879, 0.99599569005271016, 1.1989404574388258, 1.1171078899444242, 1.0156355062513667, 0.91743642525808455, 0.74067807947017739, 0.81923734426480277, 0.70467174977264058, 0.78323101456726618, 0.68175863087420818, 0.74395138216995338, 0.61956587957846299, 0.70139844707286458, 0.66211881467555178, 0.62283918227823898, 0.74067807947017739, 0.70139844707286458, 0.66211881467555178, 0.58683285258070239]

    x+= [0.92334803167467383, 0.72399377635737894, 0.50163710696501118, -0.91698018786343582, -0.7531697095140728, -0.62162493144564501, -0.45781445309628199, -0.35605339836410188, -0.45533247615159467, -0.55461155393908768, -0.61417900061158304, -0.69360226284157744, -0.7531697095140728, -0.85741274119094046, -0.93683600342093443, -1.0187412425956162, -1.055970896765926, -1.1378761359406073, -1.2396371906727872, -1.2396371906727872, -1.1180203203831087, -0.9542098420337457, -0.79536331757375733, -0.65637260867126757, -0.51241794587940315, -0.41313886809191036, -0.39576502947909908, -0.61417900061158304, -0.77302552507157141, -0.9144982109187485, -1.0758267123234242, -1.2396371906727872, -1.1751057901109172, -1.0112953117615542, -0.87478657980375174, -0.71594005534376337, -0.020986510831313865, -0.020986510831313865, -0.11778361167411933, -0.23443652807442339, -0.33123362891722885, -0.45533247615159467, -0.47767026865378059, -0.57446736949658583, -0.59432318505408444, -0.69608423978626477, -0.84252087952281651, -0.85741274119094046, -0.97654763453593163, -0.99640345009343023, -1.1180203203831087, -1.1180203203831087, -1.0956825278809228, -1.2396371906727872, -1.2396371906727872, -1.2172993981706017, -1.2197813751152891, -1.2396371906727872, -1.120502297327796, -1.0956825278809228, -1.0783086892681115, -0.95669181897843303, -0.95917379592312035, -0.83507494868875454, -0.81770111007594326, -0.69608423978626477, -0.69608423978626477, -0.69856621673095209, -0.57694934644127316, -0.57694934644127316, -0.45036852226222002, -0.35357142141941456, -0.33371560586191618, -0.23443652807442339, -0.23691850501911071, -0.11778361167411933, -0.12274756556349398, -0.038360349444125141, -0.0011306952738154852, -0.01850453388662654, -0.11778361167411933, -0.11778361167411933, -0.033396395554750491, -0.23443652807442339, -0.35108944447472723, -0.35605339836410188, -0.47518829170909327, -0.45781445309628199, -0.57446736949658583, -0.59432318505408444, -0.73579587090126153, -0.85741274119094046, -0.85244878730156581, -0.99640345009343023, -1.0162592656509288, -1.1552499745534186, -1.2172993981706017, -1.2793488217877844, -1.2594930062302858, -1.1974435826131031, -1.1552499745534186, -1.0137772887062415, -0.9740656575912443, -0.85493076424625314, -0.77054354812688408, -0.63403481616908164, -0.61417900061158304, -0.51489992282409047, -0.47518829170909327, -0.37342723697691316, -0.41313886809191036, -0.27414815918942037, -0.17486908140192781, -0.14260338112099258, -0.040842326388812467, -0.08055395750380967, -0.035878372499437816, -0.115301634729432, -0.21706268946161211, -0.25677432057660932, -0.29400397474691897, -0.33123362891722885, -0.43299468364940874, -0.53475573838158907, -0.61417900061158304, -0.71097610145438872, -0.89216041841656302]
    y+= [-0.25393667361395211, -0.26160414497230966, -0.57980420634414598, 0.89740431070474147, 0.86017465653443159, 0.84031884097693321, 0.77578744041506276, 0.53999963066976775, 0.46305834538446089, 0.40349089871196508, 0.49780602261008322, 0.44320252982696229, 0.5573734692825788, 0.47546823010789752, 0.59708510039757601, 0.51766183816758182, 0.61942289289976193, 0.5573734692825788, 0.65913452401475892, 0.50028799955477055, 0.47795020705258462, 0.43823857593758764, 0.37867112926509205, 0.34144147509478218, 0.29676589009041054, 0.36129729065228078, 0.26450018980947532, 0.24216239730728961, 0.27691007453291194, 0.31662170564790915, 0.35881531370759345, 0.39852694482259066, 0.29676589009041054, 0.25457228203072602, 0.22230658174979101, 0.20245076619229241, 0.14288331951979683, 0.043604241732304039, 0.10068971146011252, 0.043604241732304039, 0.083315872847301242, 0.021266449230118334, 0.1205455270176109, 0.05849610340042799, 0.15777518118792078, 0.10068971146011252, 0.038640287842929388, 0.1404013425751095, 0.080833895902613917, 0.17514901980073205, 0.19748681230291776, 0.12302750396229822, 0.041122264787616714, 0.1602571581326081, 0.080833895902613917, -0.0010713432720675931, -0.082976582446749103, -0.17977368328955445, -0.21948531440455155, -0.14006205217455747, -0.045746928276439336, -0.1028323980042477, -0.17977368328955445, -0.063120766889250612, -0.14006205217455747, -0.1847376371789291, -0.10035042105956038, 0.0014106336726197322, -0.040782974387064685, -0.13758007522987015, -0.080494605502061778, -0.01844518188487887, -0.12020623661705887, -0.058156812999875962, -0.15495391384268131, -0.020927158829566195, -0.095386467170185729, -0.040782974387064685, -0.14006205217455747, -0.24182310690673747, -0.19962949884705306, -0.29890857663454573, -0.31876439219204433, -0.26167892246423596, -0.32372834608141898, -0.21948531440455155, -0.26167892246423596, -0.17977368328955445, -0.21948531440455155, -0.34110218469423015, -0.28153473802173457, -0.24182310690673747, -0.34110218469423015, -0.27657078413235991, -0.38329579275391457, -0.32124636913673166, -0.4478271933157848, -0.27905276107704724, -0.54710627110327748, -0.70595279556326584, -0.58433592527358735, -0.66127721055889421, -0.56448010971608875, -0.63149348722264631, -0.49994870915421852, -0.54462429415859015, -0.44038126248172282, -0.48505684748609462, -0.38577776969860189, -0.42300742386891166, -0.52476847860109166, -0.46520103192859608, -0.50243068609890584, -0.38329579275391457, -0.42300742386891166, -0.54214231721390294, -0.70595279556326584, -0.64390337194608294, -0.60419174083108584, -0.72829058806545177, -0.56696208666077608, -0.68609698000576735, -0.64142139500139561, -0.60419174083108584, -0.72580861112076445, -0.66127721055889421, -0.72580861112076445]

    x+= [-0.29894798528614319, -0.41614686809666401, -0.37526353688369163, -0.29622242987194491, -0.19810243496081137, -0.11906132794906465, -0.012764666795336499, -0.056373553422506939, -0.11906132794906465, -0.22263243368859476, -0.27986909738675614, -0.39706798019727696, -0.49518797510841051, -0.61238685791893133, -0.51426686300779778, -0.65599574454610199, -0.7323112961436502, -0.81407795856959497, -0.77319462735662281, -0.6941535203448761, -0.6151124133331296, -0.49518797510841051, -0.45430464389543812, -0.33165465025652097, -0.27714354197255786, -0.16267021457623532, -0.11361021712066832, -0.015490222209534554, -0.059099108836705216, -0.15449354833364071, -0.21445576744600015, -0.30985020694293586, -0.41069575726826768, -0.37798909229788968, -0.47065797638062712, -0.57422908212015722, -0.49246241969421245, -0.67507463244548882, -0.77319462735662281, -0.79227351525600964, -0.91219795348072896, -0.87404017768195441, -0.97761128342148451, -1.0130435038060606, -1.1138890541313926, -1.0539268350190332, -0.97488572800728646, -0.87676573309615291, -0.78954795984181159, -0.6941535203448761]
    y+= [-1.760484960479114, -1.6596394101537819, -1.536989416514865, -1.6187560789408098, -1.4797527528167036, -1.5587938598284503, -1.4225160891185422, -1.1608627693555191, -1.3407494266925974, -1.2399038763672656, -1.4034372012191552, -1.3025916508938233, -1.4388694216037312, -1.3652794254203808, -1.5805983031420354, -1.4579483095031183, -1.4034372012191552, -1.3243960942074087, -1.2208249884678786, -1.3025916508938233, -1.1608627693555191, -1.2426294317814639, -1.1036261056573577, -1.1853927680833025, -1.021859443231413, -1.1063516610715558, -0.9646227795332516, -1.0273105540598093, -0.82561945340914566, -0.76293167888258795, -0.90466056042089216, -0.84197278589433466, -0.80108945468136228, -0.9646227795332516, -0.92373944832027921, -0.86377722920791977, -0.76293167888258795, -1.005506110746224, -0.94554389163386454, -1.038212775716602, -0.98097611201844059, -1.1635883247697172, -1.0845472177579707, -0.92646500373447749, -0.86377722920791977, -0.782010566781975, -0.82561945340914566, -0.88285611710730683, -0.78746167761037134, -0.82289389799494739]

    x+= [-1.3604327080147682, -1.3797372611268151, -1.3580196388757624, -1.3363020166247097, -1.3604327080147682, -1.4014548833778677, -1.2952798412616102, -1.3580196388757624, -0.73786087015125701, -0.8971234333256437, -1.0925820335851182]
    y+= [-0.37798741926097401, -0.21872485608658754, -0.12461515966535908, -0.042570808939159877, 0.10221333940119148, 0.17701848271037313, 0.23493214204651358, 0.31938956191171863, -0.38281355753898572, -0.44314028601413213, -0.49864087621126685]

    x+= [0.17472423942206472, -0.15952338149616896, -0.26173133169430685, -0.37775116705435474, -0.49929575647916735, -0.95508796682221364, -0.51310764164107781]
    y+= [0.17550656909658358, 0.18379370019372976, 0.1423580447079984, 0.15616992986990885, 0.20865509348516875, -0.0012855609758708475, 0.57881361582436996]

    x+= [-0.23655014601192148]
    y+= [-0.36466868316613488]

    x+= [-1.3423857967732549]
    y+= [0.038771833539803069]

    x+= [-0.15531826003447979, -0.57770285198339977, -0.71902701996630913]
    y+= [-1.7204889676185182, -1.0440384557003231, -1.1059670236928338]


    x = numpy.asarray(x)
    y = numpy.asarray(y)

    if 1:
        md = []
        for i in range(x.shape[0]):
            tx,ty = x[i],y[i]
            dist = numpy.sqrt((x-tx)**2+(y-ty)**2)
            idx=numpy.argsort(dist)
            mindist = float(dist[idx[1]]) # don't compare self
            md.append((mindist,i,idx[1], x[i],y[i]))
        md.sort()
        print 'md[:10]',repr(md[:10])
            #print 'dist[idx[0]]',dist[idx[0]]
            #print 'idx[0]',idx[0]
            #print x[idx[0]], y[idx[0]]


    print 'x=',repr(x)
    print 'y=',repr(y)
    hlong,hlat,hR = xform_stereographic_2_long_lat(x,y)
    long,lat,R = xform_heisenberg_long_lat_2_my(hlong,hlat,hR)
    #print 'long',repr(long*R2D)
    #print 'lat',repr(lat*R2D)
    #print len(lat)
    #print 'long,lat,R',long*R2D,lat*R2D,R
    hlong,hlat,hrho = xform_my_long_lat_2_heisenberg(long,lat,R)
    x,y = xform_long_lat_2_stereographic(hlong,hlat,hrho)

    ax1.plot([x],[y],'bx',mew=2)

ax1.set_xlim(im_extent[:2])
ax1.set_ylim(im_extent[2:])


class ClickGetter:
    def __init__(self):
        self.xcoords = []
        self.ycoords = []
    def on_click(self,event):
        # get the x and y coords, flip y from top to bottom
        if event.button==1:
            if event.inaxes is not None:
                print 'SAVED'
                self.xcoords.append(event.xdata)
                self.ycoords.append(event.ydata)

cg = ClickGetter()
binding_id=pylab.connect('button_press_event', cg.on_click)
pylab.show()
print 'x=',repr(cg.xcoords)
print 'y=',repr(cg.ycoords)