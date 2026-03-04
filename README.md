Install Blender 4.0.0, from here https://download.blender.org/release/Blender4.0/

conda create -n blender python=3.10
source activate blender
pip install blendertoolbox==0.0.5
pip install https://download.blender.org/pypi/bpy/bpy-4.0.0-cp310-cp310-manylinux_2_28_x86_64.whl
pip install potpourri3d numpy matplotlib

Install rembg. We first need to install onnxruntime-gpu.
pip install onnxruntime-gpu==1.20.1 --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-X/pypi/simple/ --force-reinstall
In the url set onnxruntime-cuda-X by setting "X" to your cuda version (11, 12, ...) 
You can check if the version is right here https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#cuda-11x
Then 
pip install "rembg[gpu]"
If no gpu (slower):
pip install rembg

Run the script, with glb file in your folder like:
python modular.py --glb sample.glb
 
You can open the .blend file generated to update (optional) the camera parameter and the rotation of the point cloud. 
When you find something satisfying save them in the python file.
You can click on play (bottom, center of blender, or space command) to see if the camera animation runs correctly.
If there is not enough light, try to change strength in line 110

Last thing, the script can be run everywhere, but the .blend has to be opened locally.

Then run 
python modular.py --glb shape.glb --render --full (Quite slow, you can change res and numsamples in script to accelerate things)
Add --eevee if you want fast rendering (eevee blender)
Add --gpu if you have an Nvidia GPU
Add --normals if you want normals shading 
You have option --nr from 0 to 3 to setup the prefered normals shading (logic in normals.py)
Add --sub X with X int > 0 if you want to subdivide mesh (pretty but can generate artefacts)
Change --light to any path in studio light to change the lighting