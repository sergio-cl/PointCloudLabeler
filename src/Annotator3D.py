import numpy as np
import pptk
import laspy
import tkinter
from tkinter import ttk
import multiprocessing
import time


# TODO leyenda con colores
# TODO Cerrar adecuadamente el programa

# Variable to share memory between processes
button_state = multiprocessing.Value('i')


def set_button_state(button_state, state):
    button_state.value = state


def print_button_state(button_state):
    while True:
        print(button_state.value)
        time.sleep(0.1)


def read_laz(path):
    # TODO quitar permutacion
    print('Reading laz...')
    laz_file = laspy.file.File(path, mode="r")
    print('.laz loaded')

    X, Y, Z, I = laz_file.x, laz_file.y, laz_file.z, laz_file.intensity
    n = len(X)

    idxs = np.random.permutation(range(n))
    X = X[idxs] - np.min(X)
    Y = Y[idxs] - np.min(Y)
    Z = Z[idxs] - np.min(Z)
    I = I[idxs] / np.max(I)

    return X, Y, Z, I


def save_npy(np_data, path):
    with open(path, 'wb') as f:
        np.save(f, np_data)


def read_npy(path):
    with open(path, 'rb') as f:
        np_data = np.load(f)
    return np_data

class Annotator(object):
    def __init__(self, button_state, object_classes, path_to_save):
        self.button_state = button_state
        self.object_classes = object_classes
        self.path_to_save = path_to_save

        self.viewer = None
        self.points = None
        self.point_colors = None
        self.point_colors_background = None
        self.point_size = None
        self.exit_viewer = False

        self.object_colors = np.random.rand(len(object_classes) - 1, 3)
        self.atributes = []

    def annotate(self, points, point_colors=None, point_size=0.01):
        self.points = points
        self.point_colors = point_colors
        self.point_colors_background = point_colors.copy()
        self.point_size = point_size

        self.viewer = pptk.viewer(self.points)
        if self.point_colors is not None: self.viewer.attributes(self.point_colors)
        self.viewer.set(point_size=self.point_size)

        while not self.exit_viewer:
            self.viewer.wait()
            annotation = self.viewer.get("selected")
            n_annotated = len(annotation)
            print("Annotated %d points." % n_annotated)

            button_state = self.button_state.value
            print(button_state)
            if button_state == -1:
                save_npy(self.point_colors, self.path_to_save)
                print('npy saved')
            elif n_annotated > 0:
                if button_state == 0:
                    self.point_colors[annotation] = self.point_colors_background[annotation]
                    self.viewer.attributes(point_colors, self.point_colors_background)
                elif button_state <= len(self.object_classes):
                    textured_colors = self.object_colors[button_state-1] * 1.5 * self.point_colors_background[annotation]
                    textured_colors = np.clip(textured_colors, 0, 1)
                    self.point_colors[annotation] = textured_colors
                    self.viewer.attributes(point_colors, self.point_colors_background)


def launch_annotator(points, point_colors, button_state, object_classes, path_to_save):
    annotator = Annotator(button_state, object_classes, path_to_save)
    annotator.annotate(points, point_colors)


class Gui(object):
    def __init__(self, button_state, object_classes):
        self.window = tkinter.Tk()
        self.window.configure(bg='dim gray')
        self.window.title('')
        self.window.resizable(0, 0)
        self.window.pack_slaves()

        for i, object_class in enumerate(object_classes):
            buttom = ttk.Button(self.window, text=object_class, padding=(10, 5),
                                command=lambda x=i: set_button_state(button_state, x))
            buttom.grid(column=1, row=i + 1, padx=5, pady=5)

        buttom = ttk.Button(self.window, text='save', padding=(10, 5),
                            command=lambda: set_button_state(button_state, -1))
        buttom.grid(column=1, row=i + 2, padx=5, pady=5)


        # Always on top
        self.window.lift()
        self.window.wm_attributes("-topmost", 1)

        self.window.mainloop()




if __name__ == '__main__':
    path_npy = r''
    path_to_save = r''

    object_classes = ['background', 'class1', 'class2', 'class3']

    X, Y, Z, I = read_npy(path_npy)

    n = 1000000
    X = X[:n]
    Y = Y[:n]
    Z = Z[:n]
    I = I[:n]

    points = np.stack([X, Y, Z]).T
    point_colors = np.stack([I] * 3).T

    p1 = multiprocessing.Process(target=Gui, args=(button_state, object_classes,))
    p2 = multiprocessing.Process(target=launch_annotator, args=(points, point_colors, button_state, object_classes, path_to_save,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
